"""Deterministic eligibility and scoring for style recommendations."""

from apps.styles.models import Style, StyleFabric, StyleMeasurementRequirement


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

REVIEWED_SPECIFICATION_STATUSES = {
    Style.MeasurementSpecificationStatus.REVIEWED,
    Style.MeasurementSpecificationStatus.VALIDATED,
}


def _measurement_detail(requirement):
    measurement_type = requirement.measurement_type
    detail = {'code': measurement_type.code, 'name': measurement_type.name}
    if requirement.condition.strip():
        detail['condition'] = requirement.condition
    if requirement.instructions.strip():
        detail['instructions'] = requirement.instructions
    if requirement.notes.strip():
        detail['notes'] = requirement.notes
    return detail


def rank_styles(styles, measurement_type_ids, profile_gender='', occasion=None):
    """Return ranked candidates, missing required data, and excluded styles.

    Only reviewed requirement sets can affect eligibility or measurement scores.
    Draft or absent checklists are surfaced as unknown, never treated as complete.
    """
    ranked = []
    missing_required = {}
    excluded_for_measurements = []
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

        specification_status = style.measurement_specification_status
        specification_reviewed = specification_status in REVIEWED_SPECIFICATION_STATUSES
        requirements = [
            requirement for requirement in style.measurement_requirements.all()
            if requirement.purpose in {
                StyleMeasurementRequirement.Purpose.RECOMMENDATION,
                StyleMeasurementRequirement.Purpose.BOTH,
            }
        ]
        conditional_requirements = [
            requirement for requirement in requirements if requirement.condition.strip()
        ]
        applicable_requirements = [
            requirement for requirement in requirements if not requirement.condition.strip()
        ]
        missing = [
            requirement for requirement in applicable_requirements
            if requirement.measurement_type_id not in measurement_type_ids
        ]
        missing_mandatory = [item for item in missing if item.is_required]
        if specification_reviewed and missing_mandatory:
            missing_details = [_measurement_detail(item) for item in missing_mandatory]
            for detail in missing_details:
                missing_required[detail['code']] = detail
            excluded_for_measurements.append({
                'style': style,
                'measurement_check': {
                    'status': 'incomplete',
                    'specification_status': specification_status,
                    'missing_measurements': missing_details,
                },
                'missing_measurements': missing_details,
            })
            continue

        available_scores = [
            ('fabric', SUITABILITY_SCORES[fabric_link.suitability]),
        ]
        reasons = [
            f"The recorded fabric suitability for this style is {fabric_link.get_suitability_display().lower()}."
        ]
        if fabric_link.notes.strip():
            reasons.append(f"Fabric compatibility note: {fabric_link.notes.strip()}")

        if specification_reviewed and applicable_requirements:
            measurement_score = (
                (len(applicable_requirements) - len(missing)) / len(applicable_requirements)
            ) * 100
            available_scores.append(('measurements', measurement_score))
            if missing:
                reasons.append(
                    'All reviewed required measurements are available; '
                    f'{len(missing)} optional measurement(s) are missing.'
                )
            else:
                reasons.append('All reviewed recommendation measurements are available.')
        elif specification_reviewed:
            reasons.append(
                'The reviewed specification has no recommendation-completeness measurements; '
                'measurement completeness did not affect the score.'
            )
        elif specification_status == Style.MeasurementSpecificationStatus.DRAFT:
            reasons.append(
                'The measurement checklist is a draft; measurement completeness is not used '
                'for eligibility or scoring.'
            )
        else:
            reasons.append(
                'No reviewed measurement checklist is configured; measurement completeness '
                'cannot be assessed and did not affect the score.'
            )

        if conditional_requirements:
            reasons.append(
                f'{len(conditional_requirements)} conditional measurement requirement(s) '
                'need a manual decision; their conditions are not evaluated automatically.'
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
            'fabric_compatibility': {
                'suitability': fabric_link.suitability,
                'notes': fabric_link.notes,
            },
            'missing_measurements': [_measurement_detail(item) for item in missing],
            'measurement_check': {
                'status': _measurement_status(
                    specification_status,
                    specification_reviewed,
                    applicable_requirements,
                    missing,
                    conditional_requirements,
                ),
                'specification_status': specification_status,
                'required_count': sum(item.is_required for item in applicable_requirements),
                'required_available_count': sum(
                    item.is_required and item.measurement_type_id in measurement_type_ids
                    for item in applicable_requirements
                ),
                'optional_count': sum(not item.is_required for item in applicable_requirements),
                'optional_available_count': sum(
                    not item.is_required and item.measurement_type_id in measurement_type_ids
                    for item in applicable_requirements
                ),
                'missing_measurements': [_measurement_detail(item) for item in missing],
                'conditional_requirements': [
                    _measurement_detail(item) for item in conditional_requirements
                ],
            },
        })

    ranked.sort(key=lambda item: (-item['score'], item['style'].name.casefold(), item['style'].pk))
    excluded_for_measurements.sort(
        key=lambda item: (item['style'].name.casefold(), item['style'].pk)
    )
    return (
        ranked,
        [missing_required[key] for key in sorted(missing_required)],
        excluded_for_measurements,
    )


def _measurement_status(
    specification_status,
    specification_reviewed,
    applicable_requirements,
    missing,
    conditional,
):
    if not specification_reviewed:
        return (
            'draft'
            if specification_status == Style.MeasurementSpecificationStatus.DRAFT
            else 'not_configured'
        )
    if not applicable_requirements and not conditional:
        return 'no_recommendation_requirements'
    if conditional:
        return 'conditional_unresolved'
    if missing:
        return 'optional_missing'
    return 'complete'
