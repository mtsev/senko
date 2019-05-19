class Keywords:
    def __init__(self, wordsfile):
        self.file = wordsfile
        with open(self.file) as fh:
            self.words = fh.read().splitlines()

    def add_word(self, word):
        if word not in self.words:
            self.words.append(word)
            self.update()
            return True
        return False

    def del_word(self, word):
        if word in self.words:
            self.words.remove(word)
            self.update()
            return True
        return False

    def update(self):
        with open(self.file, 'w') as fh:
            fh.write("\n".join(self.words))
