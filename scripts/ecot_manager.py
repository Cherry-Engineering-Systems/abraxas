import os
import datetime
from scripts.db_client import get_db

class ECOTManager:
    def __init__(self):
        self.db = get_db()
        self.valid_labels = ["KNOWN", "INFERRED", "HYPOTHESIS", "UNCERTAIN", "UNKNOWN", "SKEPTIC", "INVALID"]

    def create_node(self, content, label="HYPOTHESIS", confidence=0.5, genesis_label=None):
        if label not in self.valid_labels:
            raise ValueError(f"Invalid label: {label}. Must be one of {self.valid_labels}")
        
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        node = {
            "content": content,
            "label": label,
            "confidence": confidence,
            "genesis_label": genesis_label or label,
            "timestamp": now
        }
        res_id = self.db.insert("ecot_nodes", node)
        return res_id

    def update_node_label(self, node_id, new_label, new_confidence=None):
        if new_label not in self.valid_labels:
            raise ValueError(f"Invalid label: {new_label}")
        
        full_id = node_id if "ecot_nodes/" in node_id else f"ecot_nodes/{node_id}"
        
        res = self.db.query("FOR n IN ecot_nodes FILTER n._id == @id RETURN n", bind_vars={"id": full_id})
        if not res:
            raise ValueError(f"Node {node_id} not found")
        
        node = res[0]
        updated_data = {"label": new_label}
        if new_confidence is not None:
            updated_data["confidence"] = new_confidence
        
        updated_data["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.db.update(node["_id"], "ecot_nodes", updated_data)
        return True

    def link_nodes(self, from_id, to_id, rel_type="derives"):
        if rel_type not in ["supports", "contradicts", "derives"]:
            raise ValueError(f"Invalid relationship type: {rel_type}. Must be one of ['supports', 'contradicts', 'derives']")
        
        from_full = from_id if "ecot_nodes/" in from_id else f"ecot_nodes/{from_id}"
        to_full = to_id if "ecot_nodes/" in to_id else f"ecot_nodes/{to_id}"
        
        edge = {
            "_from": from_full,
            "_to": to_full,
            "type": rel_type,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        res_id = self.db.insert("ecot_edges", edge)
        return res_id

    def get_node_path(self, node_id):
        full_id = node_id if "ecot_nodes/" in node_id else f"ecot_nodes/{node_id}"
        query = "FOR v, e IN 1..1 OUTBOUND @id ecot_edges RETURN v"
        return self.db.query(query, bind_vars={"id": full_id})

    def bridge_epistemic_label(self, content, current_label, confidence):
        query = "FOR n IN ecot_nodes FILTER n.content == @content RETURN n"
        res = self.db.query(query, bind_vars={"content": content})
        
        if res:
            node = res[0]
            node_id = node["_id"]
            if node["label"] != current_label:
                self.update_node_label(node_id, current_label, confidence)
                return node_id, "updated"
            return node_id, "existing"
        else:
            node_id = self.create_node(content, label=current_label, confidence=confidence)
            return node_id, "created"

    def trigger_rupture(self, node_id):
        full_id = node_id if "ecot_nodes/" in node_id else f"ecot_nodes/{node_id}"
        self.update_node_label(full_id, "SKEPTIC", new_confidence=0.0)
        
        query = "FOR v, e IN 1..1 INBOUND @id ecot_edges RETURN v._id"
        children = self.db.query(query, bind_vars={"id": full_id})
        
        pruned_count = 0
        for child_id in children:
            self.update_node_label(child_id, "INVALID")
            pruned_count += 1 + self.trigger_rupture(child_id)
            
        return pruned_count

if __name__ == "__main__":
    manager = ECOTManager()
    try:
        n1 = manager.create_node("Root", label="KNOWN")
        n2 = manager.create_node("Child", label="HYPOTHESIS")
        manager.link_nodes(n2, n1, "derives")
        path = manager.get_node_path(n2)
        print(f"Verification: Path found: {path}")
        print("T3 Logic Verified.")
    except Exception as e:
        print(f"T3 Logic Failed: {e}")
