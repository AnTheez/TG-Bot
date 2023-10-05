import os
import random
import mysql.connector
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, PollAnswerHandler

# Import your database and token reader functions
from database.database_config import get_database_connection
from config.token_reader import get_bot_token

# Retrieve the Telegram bot token from the token.txt file
TOKEN = get_bot_token()

# Establish a database connection using the function from database_config.py
db_connection = get_database_connection()

# Initialize a dictionary to store user quiz data
user_quiz_data = {}

# Start command handler


def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    # Fetch quiz questions from the database
    cursor = db_connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM quiz_questions")
    quiz_questions = cursor.fetchall()

    if not quiz_questions:
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="No quiz questions available.")
        return

    # Shuffle the quiz questions
    random.shuffle(quiz_questions)

    # Store the shuffled questions for later use
    user_quiz_data[user_id] = {
        "remaining_questions": quiz_questions,
    }

    # Send the first quiz question
    send_next_question(update, context)

# Function to send the next quiz question


def send_next_question(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data = user_quiz_data.get(user_id)

    if user_data and user_data["remaining_questions"]:
        question_data = user_data["remaining_questions"].pop(0)
        options = [question_data["option1"], question_data["option2"],
                   question_data["option3"], question_data["option4"]]
        context.bot.send_poll(
            chat_id=update.effective_chat.id,
            question=question_data["question"],
            options=options,
            # Assuming correct_option is 1-indexed
            correct_option_id=question_data["correct_option"] - 1,
            type='quiz',
            # Assuming 'explanation' column exists in your DB
            explanation=question_data.get("explanation", "")
        )
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="Quiz complete!"
        )
        del user_quiz_data[user_id]  # Remove user data after quiz completion

# Poll answer handler


def handle_poll_answer(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data = user_quiz_data.get(user_id)

    if user_data and user_data["remaining_questions"]:
        # Get the data for the next question
        # Do not pop the question yet
        question_data = user_data["remaining_questions"][0]

        # Send the explanation for the previous question
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Explanation: {question_data['explanation']}"
        )

        # Now send the next question
        send_next_question(update, context)
    else:
        # Send the explanation for the last question
        if user_data:
            last_question_data = user_data["remaining_questions"].pop()
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Explanation: {last_question_data['explanation']}"
            )

        # Notify the user that the quiz is complete
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="Quiz complete!"
        )
        del user_quiz_data[user_id]  # Remove user data after quiz completion


# Set up the Telegram bot and handlers


def main():
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(PollAnswerHandler(handle_poll_answer))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
