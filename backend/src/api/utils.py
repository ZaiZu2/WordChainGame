import src.schemas.domain as d
import src.schemas.validation as v


def cast_v2d_rules(rules: v.DeathmatchRules) -> d.DeathmatchRules:
    """Cast Rules validation schema to corresponding domain schema."""
    if rules.type_ == d.GameTypeEnum.DEATHMATCH:
        assert isinstance(rules, v.DeathmatchRules)
        return d.DeathmatchRules(
            round_time=rules.round_time,
            start_score=rules.start_score,
            penalty=rules.penalty,
            reward=rules.reward,
        )
    else:
        raise NotImplementedError(f'Rules of type {rules.type_} are not implemented')
