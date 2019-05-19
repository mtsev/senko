class Keywords:
    def __init__(self, wordsfile):
        self.file = wordsfile
        with open(self.file) as fh:
            self.words = fh.read().splitlines()

    def add_word(self, word):
        if word not in self.words:
            self.words.append(word)
            with open(self.file, 'a') as fh:
                fh.write(word)

    def del_word(self, word):
        if word in self.words:
            self.words.remove(word)

            # Rewrite the file without the specified word
            with open(self.file, 'w') as fh:
                for w in self.words:
                    f.write(w)
