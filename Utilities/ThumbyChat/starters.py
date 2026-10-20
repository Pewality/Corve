# starters.py - EDIT THIS FILE to change the quick menu and the pickers!
#
# STARTERS = the Quick menu (press B on the chat screen).
#   Each group is ("Group name", ( "phrase", "phrase", ... )).
#   - A normal phrase is sent right away:             "tell me a joke"
#   - A phrase ending with a SPACE is a sentence
#     starter. It opens the keyboard so you finish it: "why is "
#   - A phrase ending with # is a starter that opens
#     the keyboard on the NUMBER page:                 "sqrt #"
#   Keep group names short (5 letters or so look best).
#
# CHOOSE = lists the bot shows when you say "choose a <word>".
#   ("word", ("option", "option", ...))
#   Add your own, e.g.  ("pet", ("cat", "dog", "fish"))  then say "choose a pet".

STARTERS = (
    ("Hi", (
        "hello", "how are you", "good morning", "good night", "thank you",
        "bye", "who are you", "what can you do", "what is your name",
        "i love you", "you are cool", "lol", "tell me more",
        "i am bored", "i am sad", "i am happy", "i am tired", "menu",
    )),
    ("Start", (
        "why is ", "why do ", "why does ", "why can't ", "what is ",
        "what is a ", "what are ", "what does ", "how do ", "how does ",
        "how many ", "how far is ", "how old is ", "how big is ", "who is ",
        "who invented ", "where is ", "when was ", "can you ",
        "tell me about ", "should i ", "my name is ", "i like ",
        "my favorite color is ", "capital of ", "say ", "reverse ",
        "spell ", "morse ", "shout ",
    )),
    ("Ask", (
        "why is the sky blue", "why do cats purr", "why is the ocean blue",
        "why do we sleep", "why do we dream", "why is the sea salty",
        "why is space silent", "why do we yawn", "why is grass green",
        "what is a black hole", "what is gravity", "what is python",
        "what is ai", "what is love", "what is the sun", "what is pi",
        "what is a pixel", "what is binary", "what is wifi",
        "how far is the moon", "how old is earth", "how many planets",
        "how many bones do we have", "how do planes fly",
        "how does wifi work", "how do magnets work", "how do i sleep better",
        "how do i learn code", "who invented python", "who made you",
        "who invented the telephone", "where is the eiffel tower",
        "where is the sahara", "when was python made",
        "when did man land on the moon", "capital of france",
        "capital of japan", "biggest planet", "tallest mountain",
        "fastest animal",
    )),
    ("Games", (
        "quiz", "riddle", "guess", "rps", "mathquiz", "knock knock",
        "8ball", "would you rather", "choose a game",
    )),
    ("Fun", (
        "tell me a joke", "tell me a fact", "tell me a story",
        "tell me a poem", "give me a quote", "give me a tip",
        "compliment me", "roast me", "tongue twister", "flip a coin",
        "roll d6", "roll d20", "roll 2 dice", "choose a number",
        "choose a big number", "choose a color", "choose an animal",
        "choose a food", "choose a topic", "choose a mood",
        "pizza or tacos", "cats or dogs", "random number",
    )),
    ("Math", (
        "what is #", "sqrt #", "20% of #", "prime #", "factorial #",
        "fib #", "count to #", "binary #", "hex #", "roman #",
        "5 km to miles", "10 kg to lb", "30 c to f", "100 f to c",
        "12 * 12", "100 / 8",
    )),
    ("Me", (
        "what is my name", "who am i", "what do i like",
        "what is my favorite color", "my name is ", "i like ",
        "my favorite color is ", "my favorite food is ",
        "my favorite animal is ",
    )),
    ("Tools", (
        "free ram", "uptime", "clear chat", "menu",
    )),
)

CHOOSE = (
    ("color", ("red", "orange", "yellow", "green", "blue", "purple",
               "pink", "black", "white", "brown")),
    ("animal", ("cat", "dog", "bird", "fish", "horse", "lion", "panda",
                "octopus", "owl", "dolphin", "fox", "frog")),
    ("food", ("pizza", "tacos", "burger", "pasta", "sushi", "fries",
              "ice cream", "salad", "cookie", "rice")),
    ("fruit", ("apple", "banana", "orange", "grape", "mango", "berry",
               "melon", "peach")),
    ("drink", ("water", "juice", "milk", "soda", "tea", "cocoa")),
    ("sport", ("soccer", "basketball", "tennis", "swimming", "running",
               "baseball", "skating", "biking")),
    ("season", ("spring", "summer", "fall", "winter")),
    ("day", ("monday", "tuesday", "wednesday", "thursday", "friday",
             "saturday", "sunday")),
    ("planet", ("mercury", "venus", "earth", "mars", "jupiter", "saturn",
                "uranus", "neptune")),
    ("superpower", ("flying", "invisibility", "super speed", "strength",
                    "mind reading", "time travel")),
    ("game", ("quiz", "riddle", "guess", "rps", "mathquiz", "knock knock",
              "8ball")),
    ("topic", ("joke", "fact", "story", "poem", "quote", "tip")),
    ("mood", ("happy", "sad", "tired", "bored", "excited", "hungry")),
)
