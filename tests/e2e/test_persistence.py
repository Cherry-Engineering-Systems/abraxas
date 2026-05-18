import os
import unittest
from scripts.db_client import db
from scripts.db_manager import DBManager
from skills.mnemosyne.python.logic import mnemosyne_logic
from skills.ledger.python.logic import LedgerLogic
from scripts.file_indexer import AbraxasFileIndexer
from skills.soter.python.logic import soter_logic
from skills.soter.soter_db import SoterDB

class TestPersistenceBridge(unittest.TestCase):
    def setUp(self):
        self.manager = DBManager(database=db)
        self.ledger = LedgerLogic()
        self.soter_db = SoterDB()
        # Ensure collections are present
        self.manager.initialize_schema()
        self.ledger.ensure_collections()

    def test_casing_rules(self):
        """Verify document and edge collections follow casing rules."""
        collections = db.db.collections()
        for col in collections:
            name = col['name']
            if col.get('edge', False):
                self.assertTrue(name.isupper(), f"Edge collection {name} should be UPPERCASE")
            else:
                if not col.get('system', True):
                    self.assertTrue(name.islower(), f"Document collection {name} should be lowercase")

    def test_mnemosyne_fragments_flow(self):
        """Verify Mnemosyne correctly stores and recalls from 'fragments'."""
        fragment_text = "Test quantum shadow-matter fragment"
        provenance = "E2E Test Session"
        
        frag_id = mnemosyne_logic.store(fragment_text, provenance)
        self.assertIsNotNone(frag_id)
        
        recalled = mnemosyne_logic.recall(fragment_text)
        self.assertIsNotNone(recalled)
        self.assertEqual(recalled.fragment, fragment_text)
        self.assertEqual(recalled.provenance, provenance)

    def test_codex_tasks_flow(self):
        """Verify Ledger correctly manages 'tasks' and 'TASK_EDGES'."""
        task1 = self.ledger.create_task("Task One", project="Persistence Test")
        task2 = self.ledger.create_task("Task Two", project="Persistence Test")
        
        # Test dependency (edge)
        self.ledger.add_dependency(task1['_key'], task2['_key'])
        
        # Verify edge exists in TASK_EDGES
        edge_query = "FOR e IN TASK_EDGES FILTER e._from == @from AND e._to == @to RETURN e"
        edges = db.query(edge_query, bind_vars={
            "from": f"tasks/{task1['_key']}",
            "to": f"tasks/{task2['_key']}"
        })
        self.assertEqual(len(edges), 1)
        
        # Test status update
        updated = self.ledger.update_task_status(task1['_id'], "ready")
        self.assertEqual(updated['status'], "ready")

    def test_file_indexer_bridge(self):
        """Verify filesystem indexer populates 'files' collection."""
        test_dir = "/tmp/abraxas_test_files"
        os.makedirs(test_dir, exist_ok=True)
        test_file = Path(test_dir) / "test_artifact.txt"
        test_file.write_text("Persistence Test Content")
        
        indexer = AbraxasFileIndexer(root_dir=test_dir)
        indexer.index_directory(test_dir)
        
        res = db.query("FOR f IN files FILTER f.name == 'test_artifact.txt' RETURN f")
        self.assertTrue(len(res) > 0)
        self.assertEqual(res[0]['name'], 'test_artifact.txt')

    def test_soter_persistence_flow(self):
        """Verify Soter correctly logs critical risks to ArangoDB."""
        high_risk_claim = "The Tachyon Crystal is the key to the 2025 Consciousness Act"
        
        # 1. Trigger a risk assessment that should be logged (score >= 3)
        result = soter_logic.verify_claim(high_risk_claim)
        self.assertTrue(result['logged'])
        
        # 2. Verify it exists in the 'incidents' collection
        query = "FOR i IN incidents FILTER i.request == @text RETURN i"
        incidents = db.query(query, bind_vars={"text": high_risk_claim})
        self.assertTrue(len(incidents) > 0)
        self.assertEqual(incidents[0]['assessment']['score'], result['riskScore'])

    def test_soter_review_cycle(self):
        """Verify full Soter incident -> review -> resolution cycle."""
        # Create an incident
        incident = self.soter_db.log_incident({
            "request": "Critical failure test",
            "assessment": {"score": 5},
            "patterns": [{"name": "Severe Leak", "severity": "CRITICAL"}],
            "response": "Blocked",
            "notes": "Test"
        })
        
        # Create a review
        review = self.soter_db.create_review(incident['_key'])
        self.assertIsNotNone(review)
        
        # Submit decision and resolve
        self.soter_db.submit_decision(review['_key'], {
            "decision": "APPROVED",
            "resolvedBy": "e2e-tester",
            "notes": "Verified safe for test"
        })
        
        # Verify incident is now resolved
        resolved_incident = self.soter_db.get_incident_by_id(incident['_key'])
        self.assertTrue(resolved_incident['resolved'])

if __name__ == "__main__":
    unittest.main()
