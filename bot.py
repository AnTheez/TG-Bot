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

# Initialize a dictionary to store user quiz data
user_quiz_data = {}

# Start command handler


def get_db_cursor():
    db_connection = get_database_connection()
    cursor = db_connection.cursor(dictionary=True)
    return db_connection, cursor


def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    # Establish a new connection and fetch quiz questions from the database
    try:
        db_connection, cursor = get_db_cursor()
        cursor.execute("SELECT * FROM quiz_questions")
        quiz_questions = cursor.fetchall()
    except mysql.connector.Error as err:
        print("Error fetching quiz questions:", err)
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="Error fetching quiz questions.")
        return
    finally:
        cursor.close()
        db_connection.close()

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
    # Send the next question whenever a poll answer is received
    send_next_question(update, context)

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
