# extraction_configs/patient_engagement_config.py

from models.extraction_config import ExtractionConfig
from models.extraction_field_spec import ExtractionFieldSpec


def build_patient_engagement_config() -> ExtractionConfig:
    return ExtractionConfig(
        name="Patient Engagement Paper Analysis",
        fields=[
            ExtractionFieldSpec(
                "Title", "Full title of the study as stated in the paper"
            ),
            ExtractionFieldSpec(
                "Survey Paper Fit",
                (
                    "This field represents how well we think this paper fits in to our "
                    "overall area of exploration. The goal of the overall research project is to "
                    "evaluate whether papers reporting on the use of LLMs in healthcare "
                    "incorporate patient engagement in their study, and identify the metrics "
                    "used to assess the impact of patient engagement initiatives."
                ),
            ),
            ExtractionFieldSpec(
                "Summary", "A short summary of the paper's content and findings."
            ),
            ExtractionFieldSpec(
                "Reported Engagement",
                (
                    "A short summary of whether the paper reports patient engagement "
                    "and how it does that. Please name metrics if they exist."
                ),
            ),
            ExtractionFieldSpec(
                "Author(s)",
                "List of all authors involved in the paper, in order of appearance",
            ),
            ExtractionFieldSpec(
                "Patient Co-authors",
                "Were any co-authors identified as patients or caregivers?",
            ),
            ExtractionFieldSpec(
                "Journal", "Name of the journal where the study was published"
            ),
            ExtractionFieldSpec(
                "Publication Stage",
                "Indicate if the paper is peer-reviewed, a preprint, or another stage",
            ),
            ExtractionFieldSpec(
                "Publication Date", "Official date the paper was published"
            ),
            ExtractionFieldSpec(
                "Field of Study",
                "Disciplinary or clinical field, such as primary care, oncology, or public health",
            ),
            ExtractionFieldSpec(
                "Country",
                "Country or countries where the study was conducted or primarily situated",
            ),
            ExtractionFieldSpec(
                "Type of Article",
                "Classify the article: original research, protocol, review, commentary, etc.",
            ),
            ExtractionFieldSpec(
                "Aim of Study",
                "State the main purpose or objective of the study as described by the authors",
            ),
            ExtractionFieldSpec(
                "Key Findings", "Summarize the main results or conclusions of the study"
            ),
            ExtractionFieldSpec(
                "Patient/Public Engagement (Y/N)",
                (
                    "Does the study report any meaningful or intentional involvement of patients or the public "
                    "in any phase of the research or implementation?"
                ),
            ),
            ExtractionFieldSpec(
                "Type of Engagement (Montreal Model continuum)",
                (
                    "Categorize engagement based on the Montreal Model: Information (e.g., newsletters), "
                    "Consultation (e.g., surveys, focus groups), Collaboration (e.g., co-design sessions), "
                    "or Partnership (e.g., decision-making roles, advisory boards)."
                ),
            ),
            ExtractionFieldSpec(
                "Level of Patient Involvement (Montreal Model)",
                (
                    "At what level were patients or the public involved across the research lifecycle? "
                    "Score each phase (design, development, evaluation, implementation) as: None, Information, "
                    "Consultation, Collaboration, or Partnership."
                ),
            ),
            ExtractionFieldSpec(
                "Evaluation of Impact (Y/N)",
                "Did the study evaluate or measure the effect of patient/public engagement?",
            ),
            ExtractionFieldSpec(
                "Type of Evaluation",
                "What type of method or framework was used to evaluate the impact of engagement (e.g., metrics, "
                "qualitative feedback, evaluation framework)?",
            ),
            ExtractionFieldSpec(
                "Impact of Engagement",
                "Describe any outcomes or changes attributed to patient/public engagement (e.g., design changes, "
                "improved recruitment, insights).",
            ),
            ExtractionFieldSpec(
                "Participatory Process",
                (
                    "Did the study include a participatory design process such as workshops, "
                    "co-design, or stakeholder sessions?"
                ),
            ),
            ExtractionFieldSpec(
                "Continuous Evaluation Cycles",
                "Was engagement conducted iteratively or cyclically, with feedback loops or repeated interaction?",
            ),
            ExtractionFieldSpec(
                "Implementation",
                "Did patient/public engagement influence the implementation strategy or process of the research?",
            ),
            ExtractionFieldSpec(
                "Organization of Health Care",
                (
                    "Did engagement lead to reported changes in health care delivery, "
                    "systems design, or institutional practice?"
                ),
            ),
            ExtractionFieldSpec(
                "Persuasive Design Techniques",
                (
                    "Were behavior-change strategies or persuasive technologies mentioned "
                    "(e.g., nudges, gamification, reminders)?"
                ),
            ),
            ExtractionFieldSpec(
                "Assess Impact",
                "Did the study measure outcomes or success metrics related specifically to engagement efforts?",
            ),
            ExtractionFieldSpec(
                "Information",
                "Was information provided to patients/public about the study, without "
                "involving them in decision-making?",
            ),
            ExtractionFieldSpec(
                "Consultation",
                (
                    "Was patient or public input sought (e.g., through interviews, surveys, "
                    "focus groups), without involving them in decision-making?"
                ),
            ),
            ExtractionFieldSpec(
                "Collaboration",
                (
                    "Was there shared decision-making or co-design between researchers and "
                    "participants in any phase of the study?"
                ),
            ),
            ExtractionFieldSpec(
                "Partnership",
                (
                    "Were patients/public involved across all stages with formal roles "
                    "(e.g., co-authors, advisory board, project governance)?"
                ),
            ),
            ExtractionFieldSpec(
                "Equity or Inclusivity Considerations",
                "Did the study aim to include marginalized or underrepresented groups in the engagement process?",
            ),
            ExtractionFieldSpec(
                "Ethical, Legal, and Social Implications (ELSI)",
                (
                    "Did the study address privacy, informed consent, data ethics, or cultural relevance "
                    "in its engagement or implementation approach?"
                ),
            ),
            ExtractionFieldSpec(
                "Technology Complexity / Integration Readiness",
                (
                    "Did the study evaluate how complex the technology was or how well it integrated with "
                    "existing clinical or community workflows?"
                ),
            ),
            ExtractionFieldSpec(
                "Real-World Evaluation or Deployment",
                (
                    "Was the technology evaluated or deployed in "
                    "real-world settings beyond pilot studies or lab prototypes?"
                ),
            ),
            ExtractionFieldSpec(
                "Feedback and Iterative Adaptation",
                "Was feedback from participants used in an ongoing way to adapt the design, strategy, or evaluation?",
            ),
        ],
    )
