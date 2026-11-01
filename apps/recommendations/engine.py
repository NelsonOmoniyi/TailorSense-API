"""Deterministic eligibility and scoring for style recommendations."""

from apps.styles.models import StyleFabric


SUITABILITY_SCORES = {
    StyleFabric.Suitability.EXCELLENT: 100,
    StyleFabric.Suitability.GOOD: 80,
    StyleFabric.Suitability.ACCEPTABLE: 60,
}

SCORE_WEIGHTS = {
    'fabric': 40,
    'measurements': 30,
    'occasion': 20,
}


def _measurement_detail(requirement):
    measurement_type = requirement.measurement_type
    return {'code': measurement_type.code, 'name': measurement_type.name}


def rank_styles(styles, measurement_type_ids, profile_gender='', occasion=None):
    """Return eligible, ranked candidates and missing mandatory measurements.

    Styles with contradictory recorded sizing categories, unsuitable or inactive
    fabric links, or missing required measurements are not ranked.
    """
    ranked = []
    missing_required = {}
    normalized_profile_gender = (profile_gender or '').strip().casefold()

    for style in styles:
        fabric_link = next(
            (
                link for link in style.fabric_links.all()
                if link.is_active and link.suitability in SUITABILITY_SCORES
            ),
            None,
        )
        if fabric_link is None:
            continue

        style_gender = (style.gender or '').strip().casefold()
        if normalized_profile_gender and style_gender and normalized_profile_gender != style_gender:
            continue

        requirements = list(style.measurement_requirements.all())
        missing = [
            requirement for requirement in requirements
            if requirement.measurement_type_id not in measurement_type_ids
        ]
        missing_mandatory = [item for item in missing if item.is_required]
        for requirement in missing_mandatory:
            detail = _measurement_detail(requirement)
            missing_required[detail['code']] = detail
        if missing_mandatory:
            continue

        available_scores = [
            ('fabric', SUITABILITY_SCORES[fabric_link.suitability]),
        ]
        reasons = [
            f"The recorded fabric suitability for this style is {fabric_link.get_suitability_display().lower()}."
        ]

        if requirements:
            measurement_score = (
                (len(requirements) - len(missing)) / len(requirements)
            ) * 100
            available_scores.append(('measurements', measurement_score))
            if missing:
                reasons.append(
                    'All required measurements are available; '
                    f'{len(missing)} optional measurement(s) are missing.'
                )
            else:
                reasons.append('All recorded measurement requirements are available.')
        else:
            reasons.append(
                'No measurement requirements are recorded for this style; '
                'measurements did not affect the score.'
            )

        if normalized_profile_gender and style_gender:
            reasons.append('The profile and style have matching recorded sizing categories.')
        else:
            reasons.append(
                'Sizing-category compatibility could not be verified because the profile '
                'or style has no recorded value.'
            )

        if occasion is not None:
            occasion_ids = {item.pk for item in style.occasions.all()}
            if occasion.pk in occasion_ids:
                available_scores.append(('occasion', 100))
                reasons.append(f"This style is associated with the selected {occasion.name} occasion.")
            else:
                available_scores.append(('occasion', 0))
                reasons.append(f"This style has no recorded association with the selected {occasion.name} occasion.")

        total_weight = sum(SCORE_WEIGHTS[key] for key, _ in available_scores)
        weighted_score = sum(
            SCORE_WEIGHTS[key] * score for key, score in available_scores
        ) / total_weight

        ranked.append({
            'style': style,
            'score': round(weighted_score, 1),
            'reasons': reasons,
            'missing_measurements': [
                _measurement_detail(requirement)
                for requirement in missing
            ],
        })

    ranked.sort(key=lambda item: (-item['score'], item['style'].name.casefold(), item['style'].pk))
    return ranked, [missing_required[key] for key in sorted(missing_required)]
