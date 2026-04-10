from core.batch_manager import BatchManager


class TestBatchManager:
    def test_single_batch(self):
        bm = BatchManager([f"+4850000000{i}" for i in range(10)], batch_size=20)
        assert bm.total_batches == 1
        assert len(bm.get_batch(0)) == 10

    def test_exact_split(self):
        bm = BatchManager([f"+4850000000{i}" for i in range(40)], batch_size=20)
        assert bm.total_batches == 2
        assert len(bm.get_batch(0)) == 20
        assert len(bm.get_batch(1)) == 20

    def test_uneven_split(self):
        bm = BatchManager([f"+4850000000{i}" for i in range(25)], batch_size=20)
        assert bm.total_batches == 2
        assert len(bm.get_batch(0)) == 20
        assert len(bm.get_batch(1)) == 5

    def test_empty_list(self):
        bm = BatchManager([], batch_size=20)
        assert bm.total_batches == 0

    def test_status_tracking(self):
        bm = BatchManager([f"+4850000000{i}" for i in range(25)], batch_size=20)
        assert bm.get_status(0) == "pending"
        bm.mark_sent(0)
        assert bm.get_status(0) == "sent"
        bm.mark_error(1, "Phone Link nie odpowiada")
        assert bm.get_status(1) == "error"

    def test_resume_from_first_pending(self):
        bm = BatchManager([f"+4850000000{i}" for i in range(60)], batch_size=20)
        bm.mark_sent(0)
        bm.mark_sent(1)
        assert bm.next_pending_index() == 2

    def test_resume_all_sent(self):
        bm = BatchManager([f"+4850000000{i}" for i in range(20)], batch_size=20)
        bm.mark_sent(0)
        assert bm.next_pending_index() is None

    def test_resume_skips_error(self):
        bm = BatchManager([f"+4850000000{i}" for i in range(60)], batch_size=20)
        bm.mark_sent(0)
        bm.mark_error(1, "error")
        assert bm.next_pending_index() == 1

    def test_summary(self):
        bm = BatchManager([f"+4850000000{i}" for i in range(60)], batch_size=20)
        bm.mark_sent(0)
        bm.mark_sent(1)
        bm.mark_error(2, "timeout")
        summary = bm.summary()
        assert summary["sent"] == 2
        assert summary["error"] == 1
        assert summary["pending"] == 0
        assert summary["total"] == 3
