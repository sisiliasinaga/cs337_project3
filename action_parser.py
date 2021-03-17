import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize


def parse_command(user_input):
    stop_words = set(stopwords.words('english'))
    stop_words.remove('how')
    new_user_input = user_input.replace('?', '')
    user_tokens = word_tokenize(new_user_input.lower())
    filtered_sentence = [w for w in user_tokens if w not in stop_words]

    google_link = "https://www.google.com/search?q="
    for i in range(len(filtered_sentence)):
        google_link = google_link + filtered_sentence[i]

        if i < len(filtered_sentence) - 1:
            google_link = google_link + "+"

        if filtered_sentence[i] == "how":
            google_link = google_link + "to+"

    return google_link


if __name__ == "__main__":
    example_command = "How do I preheat the oven?"
    print(parse_command(example_command))
