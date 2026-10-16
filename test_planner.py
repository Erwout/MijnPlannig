import unittest
from planner_core import Task, greedy_plan, weighted_plan, summarize, task_score

class PlannerTests(unittest.TestCase):
    def setUp(self):
        self.tasks = [
            Task("Deadline vandaag", 30, 5, 5, 4, "School", 0, False),
            Task("Korte klus", 10, 2, 2, 1, "Thuis", 2, True),
            Task("Grote opdracht", 90, 5, 3, 5, "School", 3, True),
        ]

    def test_plan_never_exceeds_available_time(self):
        plan = greedy_plan(self.tasks, 45, 3)
        self.assertLessEqual(sum(x["task"].duration for x in plan), 45)

    def test_task_that_does_not_fit_is_not_scheduled(self):
        plan = greedy_plan(self.tasks, 20, 3)
        names = [x["task"].name for x in plan]
        self.assertNotIn("Grote opdracht", names)

    def test_summary_matches_plan(self):
        plan = greedy_plan(self.tasks, 45, 3)
        summary = summarize(plan, 45)
        self.assertEqual(summary["tasks_done"], len(plan))
        self.assertEqual(summary["planned_minutes"], sum(x["task"].duration for x in plan))
        self.assertGreaterEqual(summary["free_minutes"], 0)

    def test_both_algorithms_return_valid_plans(self):
        for algorithm in (greedy_plan, weighted_plan):
            plan = algorithm(self.tasks, 60, 3)
            self.assertLessEqual(sum(x["task"].duration for x in plan), 60)

    def test_score_rejects_task_too_long(self):
        long_task = Task("Te lang", 100, 5, 5, 5, "School", 0, False)
        self.assertEqual(task_score(long_task, 5, 30), -100.0)

if __name__ == "__main__":
    unittest.main()
