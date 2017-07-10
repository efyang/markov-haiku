import scrape
import pronouncing
import itertools
import random

subreddit = "writingprompts"
num_comments = 2000
haiku_syllable_limits = [5, 7, 5]

pronouncing.init_cmu()
allowed_words = frozenset(map(lambda x: x[0], pronouncing.pronunciations))


def count_syllables(word):
    if word == "EOF" or word == "SOF":
        return 0
    else:
        phones = pronouncing.phones_for_word(word)
        return pronouncing.syllable_count(phones[0])


print("Setting up...")
# only has next word and counts for each word - not raw probabilities
base_chains = dict()
for chain in scrape.get_raw_chains(subreddit, num_comments, allowed_words):
    chain.insert(0, "SOF")
    chain.append("EOF")
    for index, word in itertools.islice(enumerate(chain), len(chain) - 1):
        next_word = chain[index + 1]
        if word in base_chains:
            if next_word in base_chains[word]:
                base_chains[word][next_word] += 1
            else:
                base_chains[word][next_word] = 1
        else:
            base_chains[word] = {next_word: 1}

# process the base chains, turning counts into fractions and adding syllable
# counts
chains = dict()
for k in base_chains.keys():
    v = base_chains[k]
    total = sum(v.values())
    # print(k, v, total)
    to_remove = list()
    for dk in v.keys():
        if len(pronouncing.phones_for_word(dk)) == 0 and dk != "EOF"\
                and dk != "SOF":
            to_remove.append(dk)
    for dk in to_remove:
        v.pop(dk)
    # transpose to make it easier later
    chains[k] = (count_syllables(k),
                 list(map(list, zip(*list(map(lambda dv: [dv, v[dv]/total], v))[::-1]))))
chains["EOF"] = (0, [])
print("Ready.")


# http://eli.thegreenplace.net/2010/01/22/weighted-random-generation-in-python
def weighted_choice_sub(weights):
    rnd = random.random() * sum(weights)
    for i, w in enumerate(weights):
        rnd -= w
        if rnd < 0:
            return i


def weighted_choice(items, weights):
    return items[weighted_choice_sub(weights)]


def generate_n_syllable_line(n, chains):
    return ' '.join(generate_n_syllable_line_recur(0, "SOF", n, chains, []))


def generate_n_syllable_line_recur(syllables, word, n, chains, current):
    # get only the possibilities that can possibly fit within the line
    maximum_next_length = n - syllables
    possible_next_words = []
    possible_next_words_prob = []
    for index, possible_word in enumerate(chains[word][1][0]):
        word_len = chains[possible_word][0]
        if word_len <= maximum_next_length:
            if not (word_len == 0 and maximum_next_length != 0):
                # EOF case
                possible_next_words.append(possible_word)
                possible_next_words_prob.append(chains[word][1][1][index])
    if len(possible_next_words) != 0:
        # recalculate probabilities
        total_p = sum(possible_next_words_prob)
        possible_next_words_prob = [p/total_p for p in possible_next_words_prob]

        next_word = weighted_choice(possible_next_words, possible_next_words_prob)
        if next_word == "EOF":
            return current

        next_word_len = chains[next_word][0]
        if next_word_len == maximum_next_length:
            return current + [next_word]

        next_ret = generate_n_syllable_line_recur(syllables + next_word_len,
                                                  next_word,
                                                  n,
                                                  chains,
                                                  current + [next_word])
        if next_ret is None:
            # remove from chains and then try again
            word_index = chains[word][1][0].index(next_word)
            del chains[word][1][0][word_index]
            del chains[word][1][1][word_index]
            return generate_n_syllable_line_recur(syllables,
                                                  word,
                                                  n,
                                                  chains,
                                                  current)
        else:
            return next_ret
    else:
        return None


def generate_lines(line_cts, chains):
    return '\n'.join([generate_n_syllable_line(ct, chains) for ct in line_cts])


def generate_haiku(chains):
    return generate_lines(haiku_syllable_limits, chains)


def verify_line(line, n, chains):
    total = 0
    for word in line.split(' '):
        total += chains[word][0]
    return total == n


while True:
    input('')
    print(generate_haiku(chains))
