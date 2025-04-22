#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from openai import OpenAI
import os
from dotenv import load_dotenv
from IPython.display import Markdown, display
import re
import time
import json


# In[ ]:


# Load environment variables
load_dotenv(override=True)
api_key = os.getenv('OPENAI_API_KEY')

# Validate API key
if not api_key:
    print("No API key was found - please head over to the troubleshooting notebook in this folder to identify & fix!")
elif not api_key.startswith("sk-proj-"):
    print("An API key was found, but it doesn't start sk-proj-; please check you're using the right key - see troubleshooting notebook")
elif api_key.strip() != api_key:
    print("An API key was found, but it looks like it might have space or tab characters at the start or end - please remove them - see troubleshooting notebook")
else:
    print("API key found and looks good so far!")


# In[ ]:

client = OpenAI(api_key=api_key)


def generate_quiz(topic, num_questions=5):
    """Generate a quiz with the specified topic and number of questions"""
    prompt = f"""Generate a multiple-choice quiz with {num_questions} questions on the topic: {topic}.
    Format the response as a JSON array of objects with the following structure:
    [
        {{
            "question": "Question text?",
            "options": ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"],
            "correct_answer": "B"
        }}
    ]
    Make sure the JSON is valid and each question has exactly 4 options (A, B, C, D).
    The correct_answer field should only contain the letter (A, B, C, or D).
    Return ONLY the JSON with no other text.
    """

    messages = [
        {"role": "system", "content": "You are a quiz generator specializing in creating educational multiple-choice quizzes. Respond with valid JSON only."},
        {"role": "user", "content": prompt}
    ]

    # Remove the response_format parameter that was causing issues
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        max_tokens=2000
    )

    content = response.choices[0].message.content

    # Try to extract and parse JSON from the response
    try:
        # First try to parse the entire content as JSON
        result = json.loads(content)
        if isinstance(result, list):
            return result
        elif "questions" in result:
            return result["questions"]
        else:
            return result
    except json.JSONDecodeError:
        # If direct parsing fails, try to extract JSON with regex
        json_match = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                # If that fails too, make a last attempt with a more flexible regex
                json_pattern = re.compile(r'(\[.*\])', re.DOTALL)
                match = json_pattern.search(content)
                if match:
                    try:
                        return json.loads(match.group(1))
                    except:
                        raise ValueError(
                            "Failed to parse quiz content as JSON")
                else:
                    raise ValueError("Could not extract JSON from response")
        else:
            raise ValueError("Failed to extract quiz content")


# In[ ]:


def present_quiz(quiz_data):
    """Present quiz questions one by one and collect user answers"""
    user_answers = {}
    total_questions = len(quiz_data)

    print(f"\n--- Quiz with {total_questions} questions ---\n")

    for i, question_data in enumerate(quiz_data):
        question = question_data["question"]
        options = question_data["options"]

        # Display question and options
        print(f"\nQuestion {i+1}/{total_questions}:")
        print(question)
        for option in options:
            print(option)

        # Get user answer
        while True:
            answer = input("\nYour answer (A, B, C, or D): ").strip().upper()
            if answer in ["A", "B", "C", "D"]:
                break
            else:
                print("Please enter A, B, C, or D.")

        user_answers[i] = answer
        print()  # Add a blank line for readability

    return user_answers


# In[ ]:


def calculate_results(quiz_data, user_answers):
    """Calculate and display quiz results"""
    correct_count = 0
    total_questions = len(quiz_data)
    results = []

    for i, question_data in enumerate(quiz_data):
        question = question_data["question"]
        options = question_data["options"]
        correct = question_data["correct_answer"]
        user_answer = user_answers.get(i, "No answer")

        is_correct = user_answer == correct
        if is_correct:
            correct_count += 1

        results.append({
            "question_num": i+1,
            "question": question,
            "options": options,
            "user_answer": user_answer,
            "correct_answer": correct,
            "is_correct": is_correct
        })

    score_percentage = (correct_count / total_questions) * 100

    return {
        "score": correct_count,
        "total": total_questions,
        "percentage": score_percentage,
        "details": results
    }


# In[ ]:


def display_results(results):
    """Display quiz results in a readable format"""
    print("\n--- Quiz Results ---")
    print(
        f"Score: {results['score']}/{results['total']} ({results['percentage']:.1f}%)")

    if results['percentage'] >= 90:
        print("Excellent job! 🌟")
    elif results['percentage'] >= 70:
        print("Good work! 👍")
    elif results['percentage'] >= 50:
        print("Not bad. Keep learning! 📚")
    else:
        print("You might need to study this topic more. Don't give up! 💪")

    print("\n--- Question Review ---")
    for item in results["details"]:
        print(f"\nQuestion {item['question_num']}: {item['question']}")
        for option in item['options']:
            print(option)

        print(f"Your answer: {item['user_answer']}")
        print(f"Correct answer: {item['correct_answer']}")

        if item['is_correct']:
            print("✓ Correct!")
        else:
            print("✗ Incorrect")


# In[ ]:


def run_quiz_session():
    """Run an interactive quiz session"""
    while True:
        # Get quiz parameters
        topic = input("\nEnter the topic for your quiz: ")

        while True:
            try:
                num_questions = int(
                    input("How many questions would you like (1-10)? "))
                if 1 <= num_questions <= 10:
                    break
                else:
                    print("Please enter a number between 1 and 10.")
            except ValueError:
                print("Please enter a valid number.")

        print(f"\nGenerating a {num_questions}-question quiz on {topic}...")

        try:
            # Generate and present quiz
            quiz_data = generate_quiz(topic, num_questions)
            user_answers = present_quiz(quiz_data)

            # Calculate and display results
            results = calculate_results(quiz_data, user_answers)
            display_results(results)

            # Ask if user wants another quiz
            again = input(
                "\nWould you like to take another quiz? (yes/no): ").strip().lower()
            if again != 'yes' and again != 'y':
                print("\nThank you for using the quiz generator! Goodbye!")
                break

        except Exception as e:
            print(f"An error occurred: {e}")
            retry = input(
                "\nWould you like to try again? (yes/no): ").strip().lower()
            if retry != 'yes' and retry != 'y':
                print("\nExiting quiz generator. Goodbye!")
                break


# To run this in your Jupyter notebook, you can either save it as a separate Python file and import it, or simply execute the code in a cell and call run_quiz_session() to start the interactive quiz.

# In[ ]:


# Run the interactive quiz session when executed
if __name__ == "__main__":
    run_quiz_session()


# In[ ]:
