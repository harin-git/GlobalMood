import pandas as pd
import json
import random
import psynet.experiment
from psynet.page import SuccessfulEndPage, InfoPage
from psynet.timeline import Timeline, PageMaker, Event, CodeBlock, join
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker
from psynet.consent import NoConsent, LucidConsent, MainConsent
from psynet.asset import LocalStorage, S3Storage
from markupsafe import Markup
from psynet.demography.general import (
    BasicDemography,
    BasicMusic,
    Income,
    Language,
    EncounteredTechnicalProblems,
)
from psynet.prescreen import WikiVocab, BeepHeadphoneTest
from .logic import CustomUnsuccessfulEndLogic

from psynet.recruiters import get_lucid_settings
from psynet.lucid.qualifications import verify_lucid_qualifications

from psynet.modular_page import AudioPrompt, ModularPage, Control
from psynet.utils import get_logger, get_translator, NoArgumentProvided
import hashlib

from .volume_calibration import get_volume_calibration_audio
from .utils import get_title_and_description


# with open("ko_dimensions.txt") as f:
#     ALL_DIMENSIONS = [line.strip() for line in f.readlines()]

LOCALE = "es"
LANGUAGE = "SPA"
COUNTRY = "MX"
LUCID_CONFIG_PATH = f"qualifications/lucid/lucid-{LANGUAGE}-{COUNTRY}.json"

WAGE_PER_HOUR = 4


# Load dimensions from CSV file, from the 'grouped_tag' column
ALL_DIMENSIONS = pd.read_csv(f"rating_dimensions/{LOCALE}_STEP_for_dense_rate.csv")["grouped_tag"].tolist()


RATE_TIME_PER_DIMENSION = 3
DIMENSIONS_PER_PARTICIPANT = 7
TRIALS_PER_PARTICIPANT = 65
N_RATINGS_PER_STIMULUS = 1000
N_REPEAT_TRIALS = 1



_ = get_translator()
_p = get_translator(context=True)



def patched_introduction(self):
    return InfoPage(
        Markup(
            "".join([
                "<p>",
                _("We will now perform a quick test to check that you are wearing headphones."),
                "</p>",
                "<p>",
                _("In each trial, you will hear three sounds separated by silences. "),
                self.task_description,
                "</p>"
            ])
        ),
        time_estimate=10,
    )

BeepHeadphoneTest.introduction = property(patched_introduction)


recruiter_settings = get_lucid_settings(
        lucid_recruitment_config_path=LUCID_CONFIG_PATH,
        termination_time_in_s= 120 * 60,
        debug_recruiter=False,
        initial_response_within_s=180,
        inactivity_timeout_in_s=15 * 60,
        no_focus_timeout_in_s=10 * 60,
        bid_incidence=66,
    )

# def get_prolific_settings():
#     with open("pt_prolific.json", "r") as f:
#         qualification = json.dumps(json.load(f))
#     return {
#         "recruiter": "prolific",
#         "base_payment": 5.5,
#         "prolific_estimated_completion_minutes": 37,
#         "prolific_recruitment_config": qualification,
#         "auto_recruit": False,
#         "wage_per_hour": 0,
#         "currency": "£",
#         "show_reward": False,
#     }
# recruiter_settings = get_prolific_settings()

data = pd.read_csv("dense_rating_stim.csv")

def make_url(track_id):
    return f"static/selected-songs/{track_id}.mp3"

start_nodes = [
    StaticNode(
        definition={
            "audio_url": make_url(row["videoID"]),
            "context": row.to_dict(),
        }
    )
    for _, row in data.iterrows()
]

def pick_dimensions(participant):
    selected_dimensions = random.sample(ALL_DIMENSIONS, DIMENSIONS_PER_PARTICIPANT)
    participant.var.set("dimensions", selected_dimensions)

# DenseRatingControl class
class DenseRatingControl(Control):
    macro = "dense_rating"
    external_template = "custom-controls.html"

    def __init__(self, dimensions, bot_response=NoArgumentProvided):
        super().__init__(bot_response=bot_response)
        dimensions = sorted(dimensions)
        hashes = [
            hashlib.sha256(dimension.encode("utf-8")).hexdigest()
            for dimension in dimensions
        ]
        self.dimension_dict = dict(zip(hashes, dimensions))

    @property
    def metadata(self):
        return self.__dict__

class DenseRatingTrial(StaticTrial):
    time_estimate = RATE_TIME_PER_DIMENSION * DIMENSIONS_PER_PARTICIPANT

    def show_trial(self, experiment, participant):
        n_trials_done = DenseRatingTrial.query.filter_by(
            participant_id=participant.id
        ).count()
        progress = f"<span style='font-size:0.8em'>{n_trials_done}/{TRIALS_PER_PARTICIPANT + N_REPEAT_TRIALS} trials completed</span>"

        url = self.definition["audio_url"]
        dimensions = participant.var.get("dimensions")

        self.var.set("dimensions", dimensions)
        return show_trial(url,dimensions, progress=progress)



def show_trial(url, dimensions, progress=""):
    prompt_text = Markup(
        _("Listen to the music clip. Rate how well each of the following tags reflects <strong>emotions expressed or conveyed</strong> by the song:")
    )
    prompt = AudioPrompt(
        url, prompt_text, loop=False, controls=True
    )

    return ModularPage(
        label="music_rating",
        prompt=prompt,
        control=DenseRatingControl(dimensions=dimensions),
        time_estimate=RATE_TIME_PER_DIMENSION * DIMENSIONS_PER_PARTICIPANT,
        events={
            "hide-next-button": Event(
                is_triggered_by="promptStart",
                delay=0.0,
                js='$("#next-button").hide();',
            ),
            "hide-submit-button": Event(
                is_triggered_by="promptStart",
                delay=0.0,
                js="document.getElementById('submit').style.visibility='hidden';"
            ),
            "show-submit-button": Event(
                is_triggered_by="promptEnd",
                delay=0.0,
                js="document.getElementById('submit').style.visibility='visible';"
            ),
        },
    )
#

# def get_practice(participant):
#     url = "static/practice.mp3"
#     dimensions = participant.var.get("dimensions")
#
#     return ModularPage(
#         label="practice_trial",
#         prompt=AudioPrompt(
#             url, "This is a practice trial. Please listen and rate the clip.", loop=True, controls=True
#         ),
#         control=DenseRatingControl(dimensions=dimensions),
#         time_estimate=RATE_TIME_PER_DIMENSION * DIMENSIONS_PER_PARTICIPANT,
#     )


def HeadphoneInstructions():
    return InfoPage(Markup(
        "".join([
            "<h4>"
            + _p("Headphone-Instructions", "Welcome to the study to describe music!")
            + "</h4>"
            + "<div class='alert alert-warning' role='warning'>"
            + _p("Headphone-Instructions", "<STRONG>Warning:</STRONG> During the experiment, it is essential to use <b>headphones</b> and remain in a quiet environment. ")
            + _p("Headphone-Instructions", "On the next page, please adjust the volume of your computer. Then, we will check if your headphones are compatible.")
            + "</div>",

        ])),
    time_estimate=5, )


def get_instructions(participant):
    dimensions = participant.var.get("dimensions")
    dimension_list = "".join([f"<li>{dim}</li>" for dim in dimensions])

    return InfoPage(Markup(
        "".join([
            "<p style='font-size: 1em; line-height: 1.5;'>"
            + _("In this study, you will <strong>listen to short music clips</strong> and <strong>evaluate how well the provided tags represent the <em style='color: #007acc;'>emotions expressed</em> in the music</strong>")
            + "</p>"
            + "<hr style='border: 1px solid #ddd; margin: 20px 0;'>"
            + "<p style='font-size: 1em; line-height: 1.5;'>"
            + _("You will rate each tag on a <strong>scale of 1 to 5</strong> based on how accurately it reflects the <strong>emotions expressed or conveyed</strong> by the song:")
            + "</p>"
            + "<ul style='font-size: 1em; line-height: 1.5; list-style-type: square; margin-left: 20px;'>"
            + "<li><strong>1</strong> - <em>" + _("Not expressing at all") + "</em></li>"
            + "<li><strong>2</strong> - <em>" + _("Slightly expressing") + "</em></li>"
            + "<li><strong>3</strong> - <em>" + _("Moderately expressing") + "</em></li>"
            + "<li><strong>4</strong> - <em>" + _("Very expressing") + "</em></li>"
            + "<li><strong>5</strong> - <em>" + _("Extremely expressing") + "</em></li>"
            + "</ul>"
            + "<hr style='border: 1px solid #ddd; margin: 20px 0;'>"
            + "<p style='font-size: 1em; line-height: 1.5;'>"
            + _("The tags you will evaluate include:")
            + "</p>"
            + "<ul style='font-size: 1em; line-height: 1.5; list-style-type: disc; margin-left: 20px; color: #007acc;'>"
            + f"{dimension_list}"
            + "</ul>"
            + "<p style='font-size: 1em; line-height: 1.5;'>"
            + _("Please take your time to carefully consider each tag before rating.")
            + "</p>"
        ])
    ), time_estimate=5)






#psynet.experiment.Experiment.UnsuccessfulEndLogic = CustomUnsuccessfulEndLogic

class Exp(psynet.experiment.Experiment):
    asset_storage = LocalStorage()
    label = "MusicRatingExperiment"

    config = {
        "recruiter": "lucid",
        "wage_per_hour": float(WAGE_PER_HOUR),
        **recruiter_settings,
        'locale': LOCALE,
        "publish_experiment": True,
        **get_title_and_description(LOCALE),
        # "title": _("Listen and Rate: Assess Emotional Tags for Songs (Chrome browser and headphones required, ~30 min"),
        #
        # "description": " ".join([
        #     _("In this experiment, you will listen to short music clips and rate how well the provided tags represent the emotions of the songs."),
        #     _("Please note that headphones are required for this study"),
        #     _("We recommend opening the experiment in an incognito window in Chrome, as some browser add-ons can interfere with the experiment."),
        #     #_("If you have any questions or concerns, please contact us through Prolific.")
        # ]),

        'initial_recruitment_size': 10,
        "auto_recruit": False,
        "show_reward": False,
        "contact_email_on_error": "computational.audition+online_running_elif@gmail.com",
        "organization_name": "Max Planck Institute for Empirical Aesthetics"
    }

    timeline = Timeline(
    verify_lucid_qualifications(LUCID_CONFIG_PATH, question_names=["TIMEOUT"]),
        LucidConsent(),
        #MainConsent(),
        CodeBlock(
            lambda participant: pick_dimensions(participant)),
        HeadphoneInstructions(),
        get_volume_calibration_audio(),
        BeepHeadphoneTest(),
        WikiVocab(
            locale= LOCALE,
            performance_threshold_per_trial=0.5,
        ),
        PageMaker(lambda participant: get_instructions(participant), time_estimate=5),
        #PageMaker(lambda participant: get_practice(participant), time_estimate=5),
        InfoPage(
            Markup(
                "<div class='alert alert-warning' role='alert'>"
                + "<h3><strong>" + _("Important Notice") + "</strong></h3>"
                + _("Please rate the tags honestly. ")
                + _("Providing inconsistent answers may result in early termination of the experiment without payment. ")
                + _("This termination will be flagged as bad data, potentially influencing your reputation score on the platform.")
                + "</div>"
            ),
            time_estimate=3
        ),
        InfoPage(
            Markup(
                "<div class='alert alert-warning' role='info'>"
                + _("You are about to start the experiment. ")
                + _("<STRONG>Please note that the submit button becomes available after the song has been played once.</STRONG>")
                + "</div>"
            ),
            time_estimate=3
        ),
        StaticTrialMaker(
            id_="music_trials",
            trial_class=DenseRatingTrial,
            nodes=start_nodes,
            target_trials_per_node=N_RATINGS_PER_STIMULUS,
            expected_trials_per_participant=TRIALS_PER_PARTICIPANT,
            max_trials_per_participant=TRIALS_PER_PARTICIPANT,
            n_repeat_trials=N_REPEAT_TRIALS,
            allow_repeated_nodes=False,
            balance_across_nodes=True,
        ),
        BasicDemography(),
        BasicMusic(),
        EncounteredTechnicalProblems(),
        SuccessfulEndPage(),
    )


logger = get_logger()
