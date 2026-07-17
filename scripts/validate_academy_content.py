import json
import sys
from collections import Counter
from pathlib import Path

CONTENT = Path('academy_content.json')
REGISTRY = Path('quality/REFERENCE_REGISTRY.json')

errors = []
warnings = []


def fail(message):
    errors.append(message)


def warn(message):
    warnings.append(message)


def load_json(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        fail(f'Missing file: {path}')
    except json.JSONDecodeError as exc:
        fail(f'Invalid JSON in {path}: {exc}')
    return {}


content = load_json(CONTENT)
registry = load_json(REGISTRY)

if not isinstance(content.get('tracks'), list):
    fail('academy_content.json must contain a tracks array')

reference_ids = {
    item.get('id')
    for item in registry.get('references', [])
    if isinstance(item, dict) and item.get('id')
}
if not reference_ids:
    fail('Reference registry contains no valid references')

lesson_ids = []
lesson_titles = []
question_texts = []
answer_counts = Counter()

for track_index, track in enumerate(content.get('tracks', [])):
    if not isinstance(track, dict):
        fail(f'Track #{track_index + 1} is not an object')
        continue
    track_id = str(track.get('id', '')).strip()
    if not track_id:
        fail(f'Track #{track_index + 1} has no id')
    if not str(track.get('title', '')).strip():
        fail(f'Track {track_id or track_index + 1} has no title')
    lessons = track.get('lessons')
    if not isinstance(lessons, list):
        fail(f'Track {track_id} has no lessons array')
        continue

    for lesson_index, lesson in enumerate(lessons):
        prefix = f'{track_id}/lesson#{lesson_index + 1}'
        if not isinstance(lesson, dict):
            fail(f'{prefix} is not an object')
            continue

        lesson_id = str(lesson.get('id', '')).strip()
        title = str(lesson.get('title', '')).strip()
        if not lesson_id:
            fail(f'{prefix} has no id')
        else:
            lesson_ids.append(lesson_id)
        if not title:
            fail(f'{prefix} has no title')
        else:
            lesson_titles.append((track_id, title.casefold()))

        summary = lesson.get('summary')
        if not isinstance(summary, list) or len(summary) < 3:
            fail(f'{prefix} must have at least 3 summary points')
        elif any(not str(item).strip() for item in summary):
            fail(f'{prefix} has an empty summary point')

        long_explanation = lesson.get('longExplanation')
        if not isinstance(long_explanation, list) or len(long_explanation) < 4:
            fail(f'{prefix} must have at least 4 longExplanation paragraphs')
        elif any(len(str(item).strip()) < 40 for item in long_explanation):
            warn(f'{prefix} contains a very short explanation paragraph')

        questions = lesson.get('questions')
        if not isinstance(questions, list) or len(questions) < 5:
            fail(f'{prefix} must have at least 5 questions')
            continue

        consecutive_answer = None
        consecutive_count = 0
        local_answers = Counter()

        for question_index, question in enumerate(questions):
            qprefix = f'{prefix}/question#{question_index + 1}'
            if not isinstance(question, dict):
                fail(f'{qprefix} is not an object')
                continue

            qtext = str(question.get('q', '')).strip()
            options = question.get('options')
            answer = question.get('answer')
            explanation = str(question.get('explanation', '')).strip()

            if not qtext:
                fail(f'{qprefix} has no question text')
            else:
                question_texts.append(qtext.casefold())
            if not isinstance(options, list) or len(options) != 4:
                fail(f'{qprefix} must have exactly 4 options')
            elif len({str(option).strip().casefold() for option in options}) != 4:
                fail(f'{qprefix} contains duplicate options')
            if not isinstance(answer, int) or answer not in range(4):
                fail(f'{qprefix} answer must be an integer from 0 to 3')
            else:
                answer_counts[answer] += 1
                local_answers[answer] += 1
                if answer == consecutive_answer:
                    consecutive_count += 1
                else:
                    consecutive_answer = answer
                    consecutive_count = 1
                if consecutive_count > 3:
                    fail(f'{qprefix} creates more than 3 identical answer positions in a row')
            if len(explanation) < 20:
                fail(f'{qprefix} explanation is too short')

        if len(local_answers) < 3 and len(questions) >= 5:
            fail(f'{prefix} uses fewer than 3 different correct-answer positions')

for lesson_id, count in Counter(lesson_ids).items():
    if count > 1:
        fail(f'Duplicate lesson id: {lesson_id}')

for (track_id, title), count in Counter(lesson_titles).items():
    if count > 1:
        fail(f'Duplicate lesson title in track {track_id}: {title}')

for qtext, count in Counter(question_texts).items():
    if count > 1:
        warn(f'Repeated question text: {qtext[:80]}')

if answer_counts:
    total_answers = sum(answer_counts.values())
    for option in range(4):
        ratio = answer_counts[option] / total_answers
        if ratio > 0.45:
            warn(f'Answer position {option} is overrepresented: {ratio:.1%}')

for message in warnings:
    print(f'WARNING: {message}')
for message in errors:
    print(f'ERROR: {message}')

if errors:
    print(f'Validation failed with {len(errors)} error(s) and {len(warnings)} warning(s).')
    sys.exit(1)

print(f'Validation passed with {len(warnings)} warning(s).')
print(f'References registered: {len(reference_ids)}')
print(f'Lessons checked: {len(lesson_ids)}')
print(f'Questions checked: {len(question_texts)}')
