"""Deterministic Help Assistant logic.

Each intent handler reads only the owned objects in ``HelpContext`` and returns
a structured answer. It never echoes raw CV/JD text, tokens, or secrets, never
guarantees hiring/salary/interview outcomes, and never answers external job
market facts. When the context is insufficient it returns a safe fallback.

Localized: when ``language="vi"`` the user-facing ``answer``, ``limitations``,
and suggestion ``label`` are Vietnamese. Machine-readable ``based_on`` /
``recommended_actions`` / ``intent`` tags and user content (job titles, skill
names) are left unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from app.services.i18n import resolve_language


SUPPORTED_INTENTS = (
    "next_best_action",
    "explain_score",
    "explain_gap",
    "suggest_learning",
    "suggest_interview_practice",
    "explain_application_status",
    "help_product_usage",
)

FALLBACK_ANSWER = "I cannot determine this from your current data."
FALLBACK_ANSWER_VI = "Tôi không thể xác định điều này từ dữ liệu hiện tại của bạn."

GLOBAL_LIMITATIONS = (
    "This assistant only uses your own saved data (target jobs, analyses, learning "
    "tasks, and interview sessions). It does not predict salaries, job-market trends, "
    "or guarantee interview or hiring outcomes."
)
GLOBAL_LIMITATIONS_VI = (
    "Trợ lý này chỉ sử dụng dữ liệu bạn đã lưu (vị trí mục tiêu, phân tích, nhiệm vụ học tập "
    "và phiên phỏng vấn). Nó không dự đoán mức lương, xu hướng thị trường lao động, hay đảm bảo "
    "kết quả phỏng vấn hoặc tuyển dụng."
)


@dataclass
class HelpContext:
    """Owned objects gathered by the route after ownership validation."""

    application: Optional[Any] = None          # target job / application row
    analysis_job: Optional[Any] = None
    readiness: Optional[Any] = None            # ReadinessResult or None
    learning_tasks: List[Any] = field(default_factory=list)
    interview_sessions: List[Any] = field(default_factory=list)
    interview_scores: List[dict] = field(default_factory=list)
    task: Optional[Any] = None
    session: Optional[Any] = None


def _missing_skill_names(analysis_job: Any) -> list[str]:
    result = getattr(analysis_job, "result_json", None) if analysis_job else None
    if not isinstance(result, dict):
        return []
    out: list[str] = []
    raw = result.get("missing_skills")
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict) and item.get("skill"):
                out.append(str(item["skill"]))
            elif isinstance(item, str):
                out.append(item)
    return out[:10]


def _fallback(intent: str, lang: str = "en") -> dict:
    return {
        "intent": intent,
        "answer": FALLBACK_ANSWER_VI if lang == "vi" else FALLBACK_ANSWER,
        "based_on": [],
        "recommended_actions": ["attach_analysis", "open_help"],
        "limitations": GLOBAL_LIMITATIONS_VI if lang == "vi" else GLOBAL_LIMITATIONS,
        "fallback_used": True,
    }


def _ok(intent: str, answer: str, based_on: list[str], actions: list[str], lang: str = "en") -> dict:
    return {
        "intent": intent,
        "answer": answer,
        "based_on": based_on,
        "recommended_actions": actions,
        "limitations": GLOBAL_LIMITATIONS_VI if lang == "vi" else GLOBAL_LIMITATIONS,
        "fallback_used": False,
    }


def _handle_next_best_action(ctx: HelpContext, lang: str = "en") -> dict:
    app = ctx.application
    if app is None:
        return _fallback("next_best_action", lang)
    title = getattr(app, "job_title", "this target job")
    if getattr(app, "best_analysis_job_id", None) is None:
        answer = (
            f"'{title}' chưa có phân tích nào được đính kèm. Hãy chạy và đính kèm một phân tích để mở khóa "
            "đánh giá mức sẵn sàng và phần chuẩn bị phù hợp."
            if lang == "vi"
            else f"'{title}' has no analysis attached yet. Run and attach an analysis to unlock readiness and tailored prep."
        )
        return _ok("next_best_action", answer, [f"target_job:{title}", "status:no_analysis"],
                   ["attach_analysis", "view_readiness"], lang)
    level = getattr(ctx.readiness, "readiness_level", None)
    if level in ("not_started", "needs_work"):
        answer = (
            f"Với '{title}', hãy tập trung thu hẹp khoảng trống kỹ năng tiếp theo — xem lại các khoảng trống "
            "và bắt đầu một nhiệm vụ học tập."
            if lang == "vi"
            else f"For '{title}', focus on closing skill gaps next — review your gaps and start a learning task."
        )
        return _ok("next_best_action", answer, [f"target_job:{title}", f"readiness:{level}"],
                   ["review_gap", "open_learning"], lang)
    if level == "almost_ready":
        answer = (
            f"'{title}' gần sẵn sàng. Hãy luyện trả lời phỏng vấn để tự tin hơn trước khi ứng tuyển."
            if lang == "vi"
            else f"'{title}' is almost ready. Practice interview answers to build confidence before applying."
        )
        return _ok("next_best_action", answer, [f"target_job:{title}", f"readiness:{level}"],
                   ["start_interview", "view_readiness"], lang)
    if level == "ready":
        answer = (
            f"'{title}' trông đã sẵn sàng. Hãy mở bộ hồ sơ ứng tuyển và luyện phỏng vấn lần cuối."
            if lang == "vi"
            else f"'{title}' looks ready. Open your application package and do a final interview practice pass."
        )
        return _ok("next_best_action", answer, [f"target_job:{title}", f"readiness:{level}"],
                   ["open_package", "start_interview"], lang)
    return _fallback("next_best_action", lang)


def _handle_explain_score(ctx: HelpContext, lang: str = "en") -> dict:
    if ctx.readiness is None or getattr(ctx.readiness, "fit_score", None) is None:
        return _fallback("explain_score", lang)
    score = getattr(ctx.readiness, "fit_score")
    level = getattr(ctx.readiness, "readiness_level", "unknown")
    title = getattr(ctx.application, "job_title", "this target job") if ctx.application else "this analysis"
    if lang == "vi":
        answer = (
            f"Điểm phù hợp của bạn cho '{title}' là {score:.0f}, tương ứng với mức sẵn sàng '{level}'. "
            "Điểm này phản ánh mức độ bằng chứng trong CV khớp với yêu cầu công việc — đây là tín hiệu chuẩn bị, "
            "không phải dự đoán tuyển dụng."
        )
    else:
        answer = (
            f"Your fit score for '{title}' is {score:.0f}, which maps to readiness '{level}'. "
            "It reflects how well your CV evidence matches the job requirements — it is a preparation signal, not a hiring prediction."
        )
    return _ok("explain_score", answer, [f"fit_score:{score:.0f}", f"readiness:{level}"],
               ["view_readiness", "review_gap"], lang)


def _handle_explain_gap(ctx: HelpContext, lang: str = "en") -> dict:
    gaps = _missing_skill_names(ctx.analysis_job)
    if not gaps:
        return _fallback("explain_gap", lang)
    if lang == "vi":
        answer = (
            "Phân tích đã đánh dấu các kỹ năng sau là còn thiếu hoặc ít bằng chứng: "
            + ", ".join(gaps)
            + ". Hãy bổ sung bằng chứng thực tế hoặc nhiệm vụ học tập cho những kỹ năng ưu tiên cao nhất."
        )
    else:
        answer = (
            "The analysis flagged these skills as missing or weakly evidenced: "
            + ", ".join(gaps)
            + ". Add real evidence or learning tasks for the highest-priority ones."
        )
    return _ok("explain_gap", answer, [f"missing_skill:{g}" for g in gaps],
               ["review_gap", "open_learning"], lang)


def _handle_suggest_learning(ctx: HelpContext, lang: str = "en") -> dict:
    if ctx.learning_tasks:
        open_tasks = [t for t in ctx.learning_tasks if getattr(t, "status", "todo") != "done"]
        if open_tasks:
            names = [getattr(t, "skill", "a skill") for t in open_tasks[:5]]
            answer = (
                "Bạn có các nhiệm vụ học tập đang mở. Hãy tiếp tục với: " + ", ".join(names) + "."
                if lang == "vi"
                else "You have open learning tasks. Continue with: " + ", ".join(names) + "."
            )
            return _ok("suggest_learning", answer,
                       [f"learning_task:{getattr(t, 'id', '')}" for t in open_tasks[:5]], ["open_learning"], lang)
        answer = (
            "Tất cả nhiệm vụ học tập đã hoàn thành. Hãy tạo lộ trình mới từ phân tích gần nhất để tiếp tục cải thiện."
            if lang == "vi"
            else "All your learning tasks are done. Generate a fresh roadmap from your latest analysis to keep improving."
        )
        return _ok("suggest_learning", answer, ["learning_tasks:all_done"], ["open_learning", "review_gap"], lang)
    gaps = _missing_skill_names(ctx.analysis_job)
    if gaps:
        answer = (
            "Chưa có nhiệm vụ học tập nào. Hãy tạo lộ trình để xử lý: " + ", ".join(gaps[:5]) + "."
            if lang == "vi"
            else "No learning tasks yet. Generate a roadmap to address: " + ", ".join(gaps[:5]) + "."
        )
        return _ok("suggest_learning", answer, [f"missing_skill:{g}" for g in gaps[:5]],
                   ["open_learning", "review_gap"], lang)
    return _fallback("suggest_learning", lang)


def _handle_suggest_interview_practice(ctx: HelpContext, lang: str = "en") -> dict:
    if ctx.interview_sessions:
        active = [s for s in ctx.interview_sessions if getattr(s, "status", "active") == "active"]
        if active:
            answer = (
                "Bạn có một phiên phỏng vấn đang hoạt động. Hãy tiếp tục trả lời câu hỏi và xem lại phản hồi theo tiêu chí."
                if lang == "vi"
                else "You have an active interview session. Continue answering questions and review your rubric feedback."
            )
            return _ok("suggest_interview_practice", answer,
                       [f"interview_session:{getattr(active[0], 'id', '')}"], ["start_interview"], lang)
        answer = (
            "Các phiên trước đã hoàn thành. Hãy bắt đầu phiên mới để giữ phong độ trả lời phỏng vấn."
            if lang == "vi"
            else "Your past sessions are complete. Start a new session to keep your interview answers sharp."
        )
        return _ok("suggest_interview_practice", answer, ["interview_sessions:completed"], ["start_interview"], lang)
    answer = (
        "Bạn chưa có phiên phỏng vấn nào. Hãy bắt đầu một phiên để luyện tập câu trả lời dựa trên CV và mô tả công việc."
        if lang == "vi"
        else "You have no interview sessions yet. Start one to practice answers grounded in your CV and the job description."
    )
    return _ok("suggest_interview_practice", answer, ["interview_sessions:none"], ["start_interview"], lang)


def _handle_explain_application_status(ctx: HelpContext, lang: str = "en") -> dict:
    app = ctx.application
    if app is None:
        return _fallback("explain_application_status", lang)
    title = getattr(app, "job_title", "this target job")
    status = getattr(app, "status", "unknown")
    if lang == "vi":
        answer = (
            f"'{title}' hiện đang ở trạng thái '{status}'. Hãy tiến triển khi bạn hoàn thành phân tích, "
            "học tập và chuẩn bị phỏng vấn."
        )
    else:
        answer = (
            f"'{title}' is currently in status '{status}'. Move it forward as you complete analysis, learning, and interview prep."
        )
    return _ok("explain_application_status", answer, [f"target_job:{title}", f"status:{status}"],
               ["update_target_job", "view_readiness"], lang)


def _handle_help_product_usage(ctx: HelpContext, lang: str = "en") -> dict:
    if lang == "vi":
        answer = (
            "Quy trình: tạo một vị trí mục tiêu, đính kèm phân tích, xem mức sẵn sàng và khoảng trống, "
            "tạo lộ trình học tập, luyện phỏng vấn, rồi mở bộ hồ sơ ứng tuyển. "
            "Dùng các nút trên mỗi trang để di chuyển giữa các bước."
        )
    else:
        answer = (
            "Workflow: create a target job, attach an analysis, review readiness and gaps, generate a learning "
            "roadmap, practice interviews, then open your application package. Use the buttons on each page to move between steps."
        )
    return _ok("help_product_usage", answer, ["help:product_workflow"], ["open_help", "view_readiness"], lang)


_HANDLERS = {
    "next_best_action": _handle_next_best_action,
    "explain_score": _handle_explain_score,
    "explain_gap": _handle_explain_gap,
    "suggest_learning": _handle_suggest_learning,
    "suggest_interview_practice": _handle_suggest_interview_practice,
    "explain_application_status": _handle_explain_application_status,
    "help_product_usage": _handle_help_product_usage,
}


def build_assistant_response(intent: str, ctx: HelpContext, *, language: str = "en") -> dict:
    lang = resolve_language(language)
    handler = _HANDLERS.get(intent)
    if handler is None:
        return _fallback(intent, lang)
    return handler(ctx, lang)


def build_suggestions(ctx: HelpContext, *, language: str = "en") -> list[dict]:
    """Context-aware list of supported intents + their product actions."""
    lang = resolve_language(language)
    if lang == "vi":
        labels = {
            "next_best_action": "Tôi nên làm gì tiếp theo?",
            "explain_score": "Giải thích điểm phù hợp của tôi",
            "explain_gap": "Khoảng trống kỹ năng của tôi là gì?",
            "suggest_learning": "Gợi ý nhiệm vụ học tập",
            "suggest_interview_practice": "Gợi ý luyện phỏng vấn",
            "explain_application_status": "Giải thích trạng thái hồ sơ ứng tuyển",
            "help_product_usage": "Sản phẩm này hoạt động như thế nào?",
        }
    else:
        labels = {
            "next_best_action": "What should I do next?",
            "explain_score": "Explain my fit score",
            "explain_gap": "What are my skill gaps?",
            "suggest_learning": "Suggest learning tasks",
            "suggest_interview_practice": "Suggest interview practice",
            "explain_application_status": "Explain my application status",
            "help_product_usage": "How does this product work?",
        }
    out: list[dict] = []
    for intent in SUPPORTED_INTENTS:
        result = build_assistant_response(intent, ctx, language=lang)
        out.append(
            {
                "intent": intent,
                "label": labels[intent],
                "recommended_actions": result["recommended_actions"],
            }
        )
    return out
