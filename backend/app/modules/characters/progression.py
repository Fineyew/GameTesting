"""Catalog-driven cumulative XP thresholds. No persistence or reward authority here."""
from bisect import bisect_right
from backend.app.modules.contracts import ContentReader


class CharacterProgression:
    def __init__(self, catalog: ContentReader):
        rules = catalog.get_definition("progression", "wayfarer").rules
        self.thresholds = tuple(rules["level_thresholds"])
        self.continued_step = rules["continued_level_step"]

    def level_for(self, experience):
        if type(experience) is not int or experience < 0:
            raise ValueError("experience must be a nonnegative integer")
        if experience >= self.thresholds[-1]:
            return len(self.thresholds) + (experience-self.thresholds[-1])//self.continued_step
        return bisect_right(self.thresholds, experience)

    def threshold_for(self, level):
        if type(level) is not int or level < 1:
            raise ValueError("level must be a positive integer")
        if level <= len(self.thresholds):
            return self.thresholds[level-1]
        return self.thresholds[-1] + (level-len(self.thresholds))*self.continued_step

    def settle(self, character):
        # Rebalancing a future threshold cannot strip levels from an existing save.
        character.level = max(character.level, self.level_for(character.experience))
