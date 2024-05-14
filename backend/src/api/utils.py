import src.schemas.domain as m  # m - domain
import src.schemas.validation as v  # v - validation


def cast_v2d_rules(rules: v.DeathmatchRules) -> m.DeathmatchRules:
    """Cast Rules validation schema to corresponding domain schema."""
    if rules.type_ == m.GameTypeEnum.DEATHMATCH:
        assert isinstance(rules, v.DeathmatchRules)
        return m.DeathmatchRules(
            round_time=rules.round_time,
            start_score=rules.start_score,
            penalty=rules.penalty,
            reward=rules.reward,
        )
    else:
        raise NotImplementedError(f'Rules of type {rules.type_} are not implemented')
