-- Append-only high-water scans exclude later inserts. Changes to an existing
-- public association or receipt invalidate outstanding evidence cursors.
CREATE TABLE finite_evidence_epoch (id INTEGER PRIMARY KEY CHECK(id=1), epoch INTEGER NOT NULL);
INSERT INTO finite_evidence_epoch VALUES(1,0);
CREATE TRIGGER finite_epoch_tasks_update AFTER UPDATE ON local_tasks BEGIN UPDATE finite_evidence_epoch SET epoch=epoch+1 WHERE id=1; END;
CREATE TRIGGER finite_epoch_tasks_delete AFTER DELETE ON local_tasks BEGIN UPDATE finite_evidence_epoch SET epoch=epoch+1 WHERE id=1; END;
CREATE TRIGGER finite_epoch_results_update AFTER UPDATE ON local_task_results BEGIN UPDATE finite_evidence_epoch SET epoch=epoch+1 WHERE id=1; END;
CREATE TRIGGER finite_epoch_results_delete AFTER DELETE ON local_task_results BEGIN UPDATE finite_evidence_epoch SET epoch=epoch+1 WHERE id=1; END;
CREATE TRIGGER finite_epoch_links_update AFTER UPDATE ON local_task_ideas BEGIN UPDATE finite_evidence_epoch SET epoch=epoch+1 WHERE id=1; END;
CREATE TRIGGER finite_epoch_links_delete AFTER DELETE ON local_task_ideas BEGIN UPDATE finite_evidence_epoch SET epoch=epoch+1 WHERE id=1; END;
CREATE TRIGGER finite_epoch_ideas_update AFTER UPDATE ON research_ideas BEGIN UPDATE finite_evidence_epoch SET epoch=epoch+1 WHERE id=1; END;
CREATE TRIGGER finite_epoch_ideas_delete AFTER DELETE ON research_ideas BEGIN UPDATE finite_evidence_epoch SET epoch=epoch+1 WHERE id=1; END;
CREATE TRIGGER finite_epoch_family_update AFTER UPDATE ON family_case_results BEGIN UPDATE finite_evidence_epoch SET epoch=epoch+1 WHERE id=1; END;
CREATE TRIGGER finite_epoch_family_delete AFTER DELETE ON family_case_results BEGIN UPDATE finite_evidence_epoch SET epoch=epoch+1 WHERE id=1; END;
CREATE TRIGGER finite_epoch_proposals_update AFTER UPDATE ON proposals BEGIN UPDATE finite_evidence_epoch SET epoch=epoch+1 WHERE id=1; END;
CREATE TRIGGER finite_epoch_proposals_delete AFTER DELETE ON proposals BEGIN UPDATE finite_evidence_epoch SET epoch=epoch+1 WHERE id=1; END;
