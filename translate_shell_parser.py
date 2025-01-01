import shlex
import subprocess


class TranslationItem:
    def __init__(self, translation, part_of_speech=None, examples=None, synonyms=None):
        self.translation = translation
        self.part_of_speech = part_of_speech or ''
        self.synonyms = synonyms or []
        self.examples = examples or []

    def __repr__(self):
        return f"TranslationItem(translation={self.translation}, part_of_speech={self.part_of_speech}, synonyms={self.synonyms}, examples={self.examples})"


class TranslateShellParser:
    def __init__(self, request):
        self.request = request
        self._current_translation = None
        self._examples = []
        self._synonyms = []

    def execute(self):
        try:
            args = shlex.split(f'trans -no-ansi {self.request}')
        except ValueError as e:
            print(f"Error in parsing request: {e}")
            raise StopIteration

        result = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0].decode('utf-8')

        lines = result.splitlines()

        if not lines:
            print("No translations found.")
            raise StopIteration

        if lines[0].strip():
            yield TranslationItem(lines[0].strip())

        current_category = None
        for line in lines[1:]:
            line = line.replace('\t', ' ' * 4)
            stripped_line = line.lstrip()
            indent_count = len(line) - len(stripped_line)

            if indent_count == 0 and stripped_line:
                current_category = stripped_line
                continue

            if current_category in ['noun', 'verb', 'adjective']:
                translation_item = self._process_translation_category(current_category, indent_count, stripped_line)
                if translation_item:
                    yield translation_item

    def _process_translation_category(self, current_category, indent_count, line):
        translation = None

        if not line or indent_count == 4:
            if self._current_translation:
                translation = TranslationItem(
                    translation=self._current_translation,
                    part_of_speech=current_category,
                    examples=self._examples,
                    synonyms=self._synonyms,
                )
            self._current_translation = None
            self._examples = []
            self._synonyms = []

        if indent_count == 4:
            if line.startswith('Synonyms: '):
                self._synonyms = [syn.strip() for syn in line[len('Synonyms: '):].split(',') if syn.strip()]
            else:
                self._current_translation = line
        elif indent_count == 8:
            if line.startswith('-'):
                self._examples.append(line[2:].strip())
            else:
                self._examples.extend([example.strip() for example in line.split(',') if example.strip()])

        return translation
