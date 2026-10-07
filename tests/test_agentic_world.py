import os
import tempfile
import unittest
from pathlib import Path

from agentic_world.guards import decide_sensitivity, new_sensitivity_card
from agentic_world.jobs import accept_job, attach_review, build_packet, create_job
from agentic_world.knowledge import INDEX
from agentic_world.pipeline import inspire_add, inspire_export, quant_advise, select_choice, transform_run, world_build
from agentic_world.registry import _validate, load_registry
from agentic_world.scaffold import accept_proposal, create_vertical, propose
from agentic_world.util import AgenticWorldError


class AgenticWorldTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._old = os.environ.get("AGENTIC_WORLD_DATA_DIR")
        os.environ["AGENTIC_WORLD_DATA_DIR"] = self._tmpdir.name

    def tearDown(self):
        if self._old is None:
            os.environ.pop("AGENTIC_WORLD_DATA_DIR", None)
        else:
            os.environ["AGENTIC_WORLD_DATA_DIR"] = self._old
        self._tmpdir.cleanup()

    def test_registry_covers_tracks_and_four_roles(self):
        registry = load_registry()
        self.assertEqual(len(registry.tracks), 4)
        self.assertEqual({item.id for item in registry.verticals}, {"novel", "comic", "game", "finance", "hotspot"})
        for vertical in registry.verticals:
            agents = {stage.agent for stage in vertical.stages}
            self.assertEqual(agents, {"product", "tech", "test", "ops"})

    def test_vertical_missing_role_fails_validation(self):
        registry = load_registry()
        novel = next(item for item in registry.verticals if item.id == "novel")
        novel.stages = [stage for stage in novel.stages if stage.agent != "ops"]
        with self.assertRaises(AgenticWorldError):
            _validate(registry)

    def test_knowledge_is_searchable(self):
        INDEX.reload()
        meta = INDEX.meta()
        self.assertGreaterEqual(meta["total"], 9)
        self.assertIn("platform", meta["categories"])
        self.assertIn("hotspot", meta["categories"])
        found = INDEX.search(q="第一性原理")
        self.assertGreaterEqual(found["count"], 1)
        self.assertIn("foundation-principles", [item["id"] for item in found["items"]])

    def test_job_packet_starts_with_charter_and_blocks_accept(self):
        packet = build_packet("finance", "test", "解释一个利率情景，不要给买卖动作")
        self.assertTrue(packet.startswith("# 干活之前"))
        self.assertIn("第一性原理", packet)
        self.assertIn("不生成实盘下单指令", packet)
        self.assertNotIn("精博", packet)
        self.assertNotIn("一凡", packet)
        self.assertNotIn("刁亮", packet)
        self.assertNotIn("豆盼", packet)
        job = create_job("novel", "product", "这条灵感要不要做成动态支线")
        with self.assertRaises(AgenticWorldError):
            accept_job(job["id"], "先选支线")
        gated = attach_review(job["id"], "外部意见：先写两条支线再选。")
        self.assertEqual(gated["status"], "gated")
        accepted = accept_job(job["id"], "成功标准：两条支线都还在，人物卡有名字。")
        self.assertEqual(accepted["status"], "accepted")

    def test_pipeline_keeps_choice_and_empty_finance_report(self):
        inspire_add("支线甲", ["novel"])
        inspire_add("支线乙", ["novel"])
        inspire_export("demo", None)
        world = world_build("演示世界")
        self.assertEqual(len(world["choices"]), 2)
        select_choice("c2", "阿宁", "想留下未选的那条路")
        bundle = transform_run(True, True)
        self.assertFalse(bundle["implicit_choice"])
        self.assertEqual(bundle["choice_id"], "c2")
        self.assertEqual(bundle["slots"]["novel"]["status"], "empty")
        self.assertNotIn("owner", bundle["slots"]["novel"])
        report = quant_advise()
        self.assertEqual(report["signals"], [])
        self.assertEqual(report["orders"], [])
        self.assertIn("不构成投资建议", report["disclaimer"])

    def test_sensitivity_defaults_to_human_review(self):
        card = new_sensitivity_card("某地选举")
        self.assertIsNone(card["touches_real_politics"])
        self.assertEqual(card["decision"], "needs_human")
        self.assertEqual(decide_sensitivity(None), "needs_human")
        self.assertEqual(decide_sensitivity(True), "needs_human")
        self.assertEqual(decide_sensitivity(False), "public")

    def test_proposal_accept_does_not_edit_target(self):
        target = Path(self._tmpdir.name) / "role.md"
        target.write_text("原文\n", encoding="utf-8")
        proposal = propose(str(target), "句子太长", "改成一句完成标准", "test")
        try:
            accepted = accept_proposal(proposal["id"])
            self.assertEqual(accepted["status"], "accepted")
            self.assertEqual(target.read_text(encoding="utf-8"), "原文\n")
            self.assertIn("没有自动改写", accepted["note"])
        finally:
            path = Path(proposal["file"])
            path.unlink(missing_ok=True)

    def test_new_vertical_file_is_validated(self):
        document = create_vertical("audio", "音频", "先做一条可重复的声音工序", "audio")
        path = Path(document["file"])
        try:
            registry = load_registry()
            self.assertIn("audio", [item.id for item in registry.verticals])
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
