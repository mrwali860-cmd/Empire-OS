"""Response formatting for Empire Brain."""


class ResponseBuilder:
    """Turn a validated plan into a readable execution contract."""

    def build(self, plan, context, orchestration_result=None):
        if plan["status"] != "READY":
            return "Unable to generate a response."

        tasks = plan.get("tasks", [])
        lines = [
            "",
            "========== EMPIRE AI ==========",
        ]

        if plan.get("plan_id"):
            lines.append(f"Plan ID: {plan['plan_id']}")

        if plan.get("goal"):
            lines.append(f"Goal: {plan['goal']}")

        if isinstance(tasks, list):
            for index, task in enumerate(tasks, start=1):
                if isinstance(task, dict):
                    lines.extend(
                        [
                            f"{index}. [{task.get('status', 'PENDING')}] {task.get('title', 'Untitled task')}",
                            f"   Action: {task.get('action', 'MANUAL_REVIEW')}",
                            f"   Permission: {'REQUIRED' if task.get('requires_permission') else 'NOT REQUIRED'}",
                            f"   Verification: {task.get('verification', 'Verify outcome before completion.')}",
                        ]
                    )
                else:
                    lines.append(f"{index}. {task}")
        else:
            lines.append(str(tasks))

        if orchestration_result is not None:
            lines.extend(
                [
                    "",
                    f"Execution Status: {str(orchestration_result.get('status', 'unknown')).upper()}",
                    f"Completed Tasks: {orchestration_result.get('completed_tasks', 0)}",
                ]
            )
            if orchestration_result.get("failed_task_id"):
                lines.append(f"Failed Task: {orchestration_result['failed_task_id']}")
            if orchestration_result.get("error"):
                lines.append(f"Execution Error: {orchestration_result['error']}")

        lines.extend(
            [
                "",
                "Status: READY FOR EXECUTION" if orchestration_result is None else "Status: EXECUTION PROCESSED",
                f"Verification: {'REQUIRED' if plan.get('verification_required', True) else 'OPTIONAL'}",
                "===============================",
                "",
            ]
        )
        return "\n".join(lines)
