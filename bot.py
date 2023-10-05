import os
import random
import mysql.connector
import time

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
            chat_id=update.effective_chat.id, text="No content available.")
        return

    # Send the first lesson material to the user (bold) if available
    lesson_material_1 = quiz_questions[0].get("material", "")
    if lesson_material_1:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*{escape_markdown_v2(lesson_material_1)}*",
            parse_mode='MarkdownV2')
        # Wait for 5 seconds before sending the next material (if exists)
        time.sleep(5)

    # Send the second lesson material to the user (italic) if available
    lesson_material_2 = quiz_questions[0].get("material_2", "")
    if lesson_material_2:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"_{escape_markdown_v2(lesson_material_2)}_",
            parse_mode='MarkdownV2')
        # Wait for 10 seconds before sending the quiz (if exists)
        time.sleep(10)

    # Shuffle the quiz questions and send the first one if they exist
    if quiz_questions:
        random.shuffle(quiz_questions)
        user_quiz_data[user_id] = {
            "remaining_questions": quiz_questions,
        }
        send_next_question(update, context)
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="Thank you for using the bot. No quiz available.")


def escape_markdown_v2(text: str) -> str:
    """Escape special characters for MarkdownV2."""
    characters_to_escape = [
        '.', '!', '-', '(', ')', '~', '>', '#', '+', '[', ']', '{', '}', '|', '*', '_', '&', '`']
    for char in characters_to_escape:
        text = text.replace(char, f'\\{char}')
    return text

# Function to send the next quiz question


def send_next_question(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data = user_quiz_data.get(user_id)

    if user_data and user_data["remaining_questions"]:
        question_data = user_data["remaining_questions"].pop(0)

        # Collect all options that are not None or empty
        options = [option for option in [question_data["option1"], question_data["option2"],
                                         question_data["option3"], question_data["option4"]] if option]

        # Ensure there are at least 2 options
        if len(options) < 2:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Error: Not enough options for the question."
            )
            return

        context.bot.send_poll(
            chat_id=update.effective_chat.id,
            question=question_data["question"],
            options=options,
            correct_option_id=options.index(
                question_data[f"option{question_data['correct_option']}"]),
            type='quiz',
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
