import os
from psynet.prescreen import HeadphoneTrial, HeadphoneTest
from typing import Optional
from os.path import exists
from psynet.utils import get_translator

_p = get_translator(context=True)


class BeepHeadphoneTrial(HeadphoneTrial):
    prompt_text = _p(
        "Beep-headphone-test",
        "Which sound is different from the other two: 1, 2, or 3?"
    )
    test_name = "beep"
    submit_early = True

class BeepHeadphoneTest(HeadphoneTest):
    def __init__(
        self,
        label="beep_headphone_test",
        media_url: Optional[str] = None,
        time_estimate_per_trial: float = 7.5,
        performance_threshold: int = 4,
        n_trials: int = 6,
    ):
        if media_url is None:
            media_url = 'static/beep_headphone_test'
            for bname, _ in self.test_definition:
                path = f"{media_url}/{bname}.wav"
                assert exists(path), f"Missing {path}"
        self.setup(
            label, media_url, time_estimate_per_trial, performance_threshold, n_trials
        )

    @property
    def test_name(self):
        return "beep"

    # @property
    # def test_definition(self):
    #     return [
    #         ("3444", "1"),
    #         ("3445", "2"),
    #         ("3446", "3"),
    #         ("3447", "1"),
    #         ("3448", "2"),
    #         ("3449", "3"),
    #     ]

    @property
    def test_definition(self):
        return [
            ("3444", "1"),
            ("3445", "2"),
            ("3446", "3"),
            ("3444", "1"),
            ("3445", "2"),
            ("3446", "3"),
        ]

    @property
    def task_description(self):
        return (
            "Your task will be to judge <strong> which sound is the odd one out.</strong>"
        )

    def get_trial_class(self, node=None, participant=None, experiment=None):
        return BeepHeadphoneTrial