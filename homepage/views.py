# homepage/views.py

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
import imaplib
import email
from email.header import decode_header
import smtplib  
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import speech_recognition as sr
from gtts import gTTS
from pygame import mixer
import os
import re
import uuid
import PyPDF2
import docx

import io
from gtts import gTTS
import pygame

import mimetypes
from email.mime.base import MIMEBase
from email import encoders

def text_to_speech(text):
    """Convert text to speech and play it directly from memory without saving any files."""
    try:
        # Convert text to speech (in memory)
        mp3_fp = io.BytesIO()
        tts = gTTS(text=text, lang='en', slow=False)
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)

        # Initialize pygame mixer once
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        # Load and play from memory
        pygame.mixer.music.load(mp3_fp, 'mp3')
        pygame.mixer.music.play()

        # Wait for playback to finish
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.unload()

    except Exception as e:
        print(f"An error occurred in text_to_speech: {e}")

def speech_to_text(duration=5):
    """Listens for speech and converts it to text."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=1)
        try:
            # Play notification sound before listening
            mixer.pre_init(44100, -16, 2, 512)
            mixer.init()

            mixer.music.load('speak.mp3')
            mixer.music.play()
            while mixer.music.get_busy():
                continue
            mixer.music.stop()
            mixer.quit()
        except Exception as e:
            print(f"Could not play speak.mp3 notification: {e}")

        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=duration)
            response = r.recognize_google(audio)
            print("RECOGNIZED:", response)
            return response
        except sr.UnknownValueError:
            text_to_speech("Sorry, I could not understand that.")
            return None
        except sr.RequestError as e:
            text_to_speech("Could not request results; check your connection.")
            print(f"Speech recognition error: {e}")
            return None

# def speech_to_text(duration=5):

#     r = sr.Recognizer()

#     with sr.Microphone() as source:

#         print("Listening...")

#         r.adjust_for_ambient_noise(source, duration=1)

#         try:

#             audio = r.listen(source, timeout=5, phrase_time_limit=duration)

#             print("Recognizing...")

#             response = r.recognize_google(audio)

#             print("RECOGNIZED:", response)

#             return response


#         except sr.UnknownValueError:

#             print("Not understood")

#             text_to_speech("Sorry, I could not understand that.")

#             return None


#         except sr.RequestError as e:

#             print("API error:", e)

#             text_to_speech("Internet error.")

#             return None

def get_confirmed_speech_input(prompt, duration=10):

    while True:

        text_to_speech(prompt)

        response = speech_to_text(duration)

        print("USER SAID:", response)


        if response:

            text_to_speech(
                f"You said {response}. Say yes to confirm or no to repeat."
            )

            confirmation = speech_to_text(6)

            print("CONFIRMATION:", confirmation)


            if confirmation:

                confirmation = confirmation.lower()


                # ✅ ACCEPT ANY YES SENTENCE
                yes_words = ["yes", "yeah", "correct", "yep", "confirm", "right", "yes correct", "yes confirm"]

                no_words = ["no", "wrong", "incorrect", "nope"]


                if any(word in confirmation for word in yes_words):

                    text_to_speech("Confirmed")

                    return response


                elif any(word in confirmation for word in no_words):

                    text_to_speech("Okay, please speak again.")

                    continue


        text_to_speech("I did not hear confirmation. Please try again.")

def convert_special_char(text):
    """Cleans up spoken email addresses and passwords."""
    text = text.lower().replace(' ', '')
    replacements = {
        'attherate': '@', 'dot': '.', 'underscore': '_', 'dollar': '$', 'hash': '#',
        'star': '*', 'plus': '+', 'minus': '-', 'dash': '-'
    }
    for word, char in replacements.items():
        text = text.replace(word, char)
    return text

def get_email_connections(request):

    email_address = request.session.get('email_address')
    app_password = request.session.get('app_password')

    print("DEBUG EMAIL:", email_address)
    print("DEBUG PASS:", app_password)

    if not email_address or not app_password:
        print("Session missing")
        return None, None

    try:

        smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
        smtp_server.starttls()
        smtp_server.login(email_address, app_password)

        imap_server = imaplib.IMAP4_SSL('imap.gmail.com')
        imap_server.login(email_address, app_password)

        print("Login success")

        return smtp_server, imap_server

    except Exception as e:

        print("Login failed:", e)

        return None, None

        
def clean_header(header):
    """Decodes email headers to a readable string."""
    if header is None:
        return ""
    decoded_header = decode_header(header)
    header_parts = []
    for part, encoding in decoded_header:
        if isinstance(part, bytes):
            header_parts.append(part.decode(encoding or 'utf-8', 'ignore'))
        else:
            header_parts.append(part)
    return "".join(header_parts)


# def login_view(request):
#     """Handles voice-based login only and stores session properly."""

#     if request.method == 'POST':

#         text_to_speech("Welcome to Voice Based Email. Please log in to continue.")


#         # -------- GET EMAIL --------

#         email_address = get_confirmed_speech_input(
#             "Please say your full email address.", duration=15)

#         if not email_address:

#             text_to_speech("I could not understand your email.")

#             return render(request, 'homepage/login.html')


#         cleaned_email = convert_special_char(email_address)



#         # -------- GET APP PASSWORD --------

#         text_to_speech("Please say your Gmail App Password.")


#         password = get_confirmed_speech_input(
#             "Speak your app password.", duration=30)


#         if not password:

#             text_to_speech("I could not understand your password.")

#             return render(request, 'homepage/login.html')


#         cleaned_password = convert_special_char(password)



#         # -------- VERIFY LOGIN --------

#         try:

#             # IMAP LOGIN TEST

#             imap_server = imaplib.IMAP4_SSL('imap.gmail.com')

#             imap_server.login(cleaned_email, cleaned_password)

#             imap_server.logout()



#             # SMTP LOGIN TEST

#             smtp_server = smtplib.SMTP('smtp.gmail.com', 587)

#             smtp_server.starttls()

#             smtp_server.login(cleaned_email, cleaned_password)

#             smtp_server.quit()



#             # -------- SAVE SESSION PROPERLY --------

#             request.session['email_address'] = cleaned_email

#             request.session['app_password'] = cleaned_password


#             # VERY IMPORTANT (prevents session expire)

#             request.session.modified = True

#             request.session.save()



#             print("SESSION SAVED:", request.session['email_address'])



#             text_to_speech("Login successful. Welcome.")



#             return redirect('homepage:options')



#         except Exception as e:

#             print("LOGIN ERROR:", e)

#             text_to_speech("Login failed. Invalid email or app password.")

#             return render(request, 'homepage/login.html')



#     return render(request, 'homepage/login.html')

# def login_view(request):
#     email_value = ""
#     password_value = ""

#     if request.method == 'POST':

#         text_to_speech("Welcome to Voice Based Email. Please log in to continue.")

#         # -------- GET EMAIL --------
#         email_address = get_confirmed_speech_input(
#             "Please say your full email address.", duration=15)

#         if not email_address:
#             text_to_speech("I could not understand your email.")
#             return render(request, 'homepage/login.html')

#         cleaned_email = convert_special_char(email_address)
#         email_value = cleaned_email   # ✅ store for frontend

#         # -------- GET PASSWORD --------
#         text_to_speech("Please say your Gmail App Password.")

#         password = get_confirmed_speech_input(
#             "Speak your app password.", duration=30)

#         if not password:
#             text_to_speech("I could not understand your password.")
#             return render(request, 'homepage/login.html', {
#                 'email_value': email_value
#             })

#         cleaned_password = convert_special_char(password)
#         password_value = cleaned_password   # ✅ store for frontend

#         # -------- VERIFY LOGIN --------
#         try:
#             imap_server = imaplib.IMAP4_SSL('imap.gmail.com')
#             imap_server.login(cleaned_email, cleaned_password)
#             imap_server.logout()

#             smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
#             smtp_server.starttls()
#             smtp_server.login(cleaned_email, cleaned_password)
#             smtp_server.quit()

#             request.session['email_address'] = cleaned_email
#             request.session['app_password'] = cleaned_password

#             request.session.modified = True
#             request.session.save()

#             text_to_speech("Login successful. Welcome.")

#             return redirect('homepage:options')

#         except Exception as e:
#             print("LOGIN ERROR:", e)
#             text_to_speech("Login failed. Invalid email or app password.")

#             # ✅ send values back to HTML
#             return render(request, 'homepage/login.html', {
#                 'email_value': email_value,
#                 'password_value': password_value
#             })

#     return render(request, 'homepage/login.html')
def login_view(request):

    # 🧹 CLEAR OLD SESSION when opening login page
    if request.method == 'GET':
        request.session.pop('email_value', None)
        request.session.pop('password_value', None)
        request.session.pop('email_done', None)
        request.session.pop('password_done', None)

    email_value = request.session.get('email_value', '')
    password_value = request.session.get('password_value', '')

    # -------- STEP 1: GET EMAIL --------
    if request.method == 'POST' and not request.session.get('email_done'):

        text_to_speech("Welcome. Please say your email address.")

        email_address = get_confirmed_speech_input(
            "Please say your full email address.", duration=15
        )

        if not email_address:
            text_to_speech("I could not understand your email.")
            return render(request, 'homepage/login.html')

        cleaned_email = convert_special_char(email_address)

        request.session['email_value'] = cleaned_email
        request.session['email_done'] = True

        text_to_speech(f"You said {cleaned_email}")

        return render(request, 'homepage/login.html', {
            'email_value': cleaned_email
        })

    # -------- STEP 2: GET PASSWORD --------
    elif request.method == 'POST' and request.session.get('email_done') and not request.session.get('password_done'):

        text_to_speech("Now please say your password.")

        password = get_confirmed_speech_input(
            "Please say your app password.", duration=20
        )

        if not password:
            text_to_speech("I could not understand your password.")
            return render(request, 'homepage/login.html', {
                'email_value': email_value
            })

        cleaned_password = convert_special_char(password)

        request.session['password_value'] = cleaned_password
        request.session['password_done'] = True

        text_to_speech("Password received.")

        return render(request, 'homepage/login.html', {
            'email_value': email_value,
            'password_value': cleaned_password
        })

    # -------- STEP 3: LOGIN --------
    elif request.method == 'POST' and request.session.get('email_done') and request.session.get('password_done'):

        cleaned_email = request.session.get('email_value')
        cleaned_password = request.session.get('password_value')

        text_to_speech("Logging you in. Please wait.")

        try:
            # IMAP
            import imaplib
            imap_server = imaplib.IMAP4_SSL('imap.gmail.com')
            imap_server.login(cleaned_email, cleaned_password)
            imap_server.logout()

            # SMTP
            import smtplib
            smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
            smtp_server.starttls()
            smtp_server.login(cleaned_email, cleaned_password)
            smtp_server.quit()

            # Save final session
            request.session['email_address'] = cleaned_email
            request.session['app_password'] = cleaned_password

            # 🧹 CLEAR TEMP SESSION
            request.session.pop('email_value', None)
            request.session.pop('password_value', None)
            request.session.pop('email_done', None)
            request.session.pop('password_done', None)

            text_to_speech("Login successful. Welcome.")

            return redirect('homepage:options')

        except Exception as e:
            print("LOGIN ERROR:", e)

            text_to_speech("Login failed. Invalid email or password.")
            text_to_speech("Do you want to try again? Say yes or no.")

            retry = get_confirmed_speech_input("Say yes or no", duration=5)

            if retry and "yes" in retry.lower():
                # 🧹 RESET SESSION
                request.session.pop('email_value', None)
                request.session.pop('password_value', None)
                request.session.pop('email_done', None)
                request.session.pop('password_done', None)

                return redirect('homepage:login')
            else:
                text_to_speech("Login cancelled.")
                return render(request, 'homepage/login.html', {
                    'email_value': cleaned_email,
                    'password_value': cleaned_password
                })

    # -------- DEFAULT --------
    return render(request, 'homepage/login.html', {
        'email_value': email_value,
        'password_value': password_value
    })



def options_view(request):
    """Provides user with main menu options after logging in."""
    if 'email_address' not in request.session:
        return redirect('login_view')

    if request.method == 'POST':
        prompt = "What would you like to do? Say 'compose', 'inbox', 'sent messages', 'trash or garbage', 'delete', 'labels' or 'logout'."
        text_to_speech(prompt)
        action = speech_to_text(5)  # listen for voice command
        
        if action:
            action = action.lower()
            if 'compose' in action:
                return JsonResponse({'result': 'compose'})
            if 'inbox' in action:
                return JsonResponse({'result': 'inbox'})
            if 'sent' in action or 'messages' in action:
                return JsonResponse({'result': 'sent'})
            if 'trash' in action or 'garbage' in action:
                return JsonResponse({'result': 'trash'})
            if 'delete' in action or 'remove' in action:  # supports both words
                return JsonResponse({'result': 'delete'})
            if 'label' in action :
                text_to_speech("Opening label section")
                return JsonResponse({'result': 'label'})
            if 'log out' in action or 'logout' in action:
                request.session.flush()
                text_to_speech("You have been successfully logged out.")
                return JsonResponse({'result': 'logout'})
        
        # If none matched, ask user to try again
        text_to_speech("Invalid action. Please try again.")
        return JsonResponse({'result': 'failure'})

    return render(request, 'homepage/options.html')



# def compose_view(request):
#     """Handles composing and sending a new email."""
#     if 'email_address' not in request.session: return redirect('login_view')
#     if request.method == 'POST':
#         smtp, _ = get_email_connections(request)
#         if not smtp:
#             text_to_speech("Your session may have expired. Please log in again.")
#             return JsonResponse({'result': 'logout'})
#         from_address = request.session['email_address']
        
#         recipient_str = get_confirmed_speech_input("Who is the recipient?", duration=15)
#         recipient = convert_special_char(recipient_str)
#         subject = get_confirmed_speech_input("What is the subject?", duration=20)
#         body = get_confirmed_speech_input("What should the email say?", duration=60)

#         msg = MIMEMultipart()
#         msg['From'] = from_address
#         msg['To'] = recipient
#         msg['Subject'] = subject
#         msg.attach(MIMEText(body, 'plain'))
        
#         try:
#             smtp.sendmail(from_address, [recipient], msg.as_string())
#             text_to_speech("Your email has been sent successfully.")
#             smtp.quit()
#             return JsonResponse({'result': 'success'})
#         except Exception as e:
#             print(f"Failed to send email: {e}")
#             text_to_speech("Sorry, your email could not be sent.")
#             smtp.quit()
#             return JsonResponse({'result': 'failure'})
#     return render(request, 'homepage/compose.html')

def compose_view(request):

    # ---------- SESSION CHECK ----------
    if 'email_address' not in request.session:
        text_to_speech("Your login session expired. Please login again.")
        return redirect('homepage:login')

    # 🧹 RESET on fresh load
    if request.method == 'GET':
        request.session.pop('recipient', None)
        request.session.pop('subject', None)
        request.session.pop('body', None)
        request.session.pop('attachment', None)
        request.session.pop('step', None)

    step = request.session.get('step', 1)

    # -------- STEP 1: RECIPIENT --------
    if request.method == 'POST' and step == 1:

        text_to_speech("Who is the recipient?")
        recipient_voice = get_confirmed_speech_input("Say recipient email", 15)

        if not recipient_voice:
            text_to_speech("Recipient not received.")
            return render(request, 'homepage/compose.html')

        recipient = convert_special_char(recipient_voice)

        request.session['recipient'] = recipient
        request.session['step'] = 2

        return render(request, 'homepage/compose.html', {
            'recipient': recipient
        })

    # -------- STEP 2: SUBJECT --------
    elif request.method == 'POST' and step == 2:

        text_to_speech("What is the subject?")
        subject = get_confirmed_speech_input("Say subject", 20) or ""

        request.session['subject'] = subject
        request.session['step'] = 3

        return render(request, 'homepage/compose.html', {
            'recipient': request.session.get('recipient'),
            'subject': subject
        })

    # -------- STEP 3: BODY --------
    elif request.method == 'POST' and step == 3:

        text_to_speech("What should the email say?")
        body = get_confirmed_speech_input("Say body", 60) or ""

        request.session['body'] = body
        request.session['step'] = 4

        return render(request, 'homepage/compose.html', {
            'recipient': request.session.get('recipient'),
            'subject': request.session.get('subject'),
            'body': body
        })

    # -------- STEP 4: ASK ATTACHMENT --------
    elif request.method == 'POST' and step == 4:

        text_to_speech("Do you want to attach a file? Say yes or no.")
        choice = get_confirmed_speech_input("Say yes or no", 5)

        if choice and "yes" in choice.lower():
            request.session['step'] = 5
        else:
            request.session['step'] = 6  # skip to send

        return render(request, 'homepage/compose.html', {
            'recipient': request.session.get('recipient'),
            'subject': request.session.get('subject'),
            'body': request.session.get('body')
        })

    # -------- STEP 5: GET FILE NAME --------
    elif request.method == 'POST' and step == 5:

        text_to_speech("Please say the file name with extension.")
        filename_voice = get_confirmed_speech_input("Say file name", 10)

        if filename_voice:
            filename = convert_special_char(filename_voice)
            filepath = os.path.join(settings.BASE_DIR, "attachments", filename)

            if os.path.exists(filepath):
                request.session['attachment'] = filepath
                text_to_speech("File attached successfully.")
            else:
                text_to_speech("File not found. Sending without attachment.")

        request.session['step'] = 6

        return render(request, 'homepage/compose.html', {
            'recipient': request.session.get('recipient'),
            'subject': request.session.get('subject'),
            'body': request.session.get('body')
        })

    # -------- STEP 6: SEND EMAIL --------
    elif request.method == 'POST' and step == 6:

        text_to_speech("Sending your email. Please wait.")

        try:
            from_address = request.session['email_address']
            recipient = request.session['recipient']
            subject = request.session['subject']
            body = request.session['body']

            msg = MIMEMultipart()
            msg['From'] = from_address
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            # 📎 ATTACH FILE IF EXISTS
            filepath = request.session.get('attachment')

            if filepath and os.path.exists(filepath):
                with open(filepath, 'rb') as file:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(file.read())

                encoders.encode_base64(part)

                filename = os.path.basename(filepath)
                part.add_header('Content-Disposition', f'attachment; filename={filename}')

                msg.attach(part)

            smtp = smtplib.SMTP('smtp.gmail.com', 587)
            smtp.starttls()
            smtp.login(
                request.session['email_address'],
                request.session['app_password']
            )

            smtp.send_message(msg)
            smtp.quit()

            text_to_speech("Email sent successfully.")

            # 🧹 CLEAR SESSION
            request.session.pop('recipient', None)
            request.session.pop('subject', None)
            request.session.pop('body', None)
            request.session.pop('attachment', None)
            request.session.pop('step', None)

            return redirect('homepage:options')

        except Exception as e:
            print("Send error:", e)
            text_to_speech("Failed to send email.")
            return render(request, 'homepage/compose.html')

    # -------- DEFAULT --------
    return render(request, 'homepage/compose.html', {
        'recipient': request.session.get('recipient', ''),
        'subject': request.session.get('subject', ''),
        'body': request.session.get('body', '')
    })

def read_emails(imap, email_ids, max_to_read=5):
    """Helper function to read and announce a list of emails."""
    if not email_ids:
        text_to_speech("This folder is empty.")
        return

    # Read the most recent emails first
    emails_to_read = email_ids[-max_to_read:]
    emails_to_read.reverse()

    text_to_speech(f"Showing the latest {len(emails_to_read)} emails.")
    
    for mail_id in emails_to_read:
        status, data = imap.fetch(mail_id, '(RFC822)')
        raw_email = data[0][1]
        message = email.message_from_bytes(raw_email)
        
        from_ = clean_header(message['From'])
        subject = clean_header(message['Subject'])
        
        text_to_speech(f"Email from: {from_}. Subject: {subject}.")
        # Here you could add logic to ask the user if they want to read the body, reply, etc.

def _speak_chunks(text, chunk_size=500):
    # Helper: speak long text in chunks so TTS doesn't choke
    for i in range(0, len(text), chunk_size):
        text_to_speech(text[i:i+chunk_size])

def _extract_plaintext(msg):
    # Helper: get readable body from an email.message.Message
    if msg.is_multipart():
        parts = []
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = part.get("Content-Disposition", "")
            if ctype == "text/plain" and "attachment" not in (disp or "").lower():
                try:
                    parts.append(part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="ignore"))
                except Exception:
                    continue
        return "\n".join(parts).strip()
    else:
        try:
            return msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8", errors="ignore").strip()
        except Exception:
            return ""

def sent_view(request):
    """
    Reads the 5 latest emails from the Sent folder and announces:
      - Recipient (To)
      - Subject
      - Date and Time
    """
    if 'email_address' not in request.session:
        return redirect('login_view')

    if request.method == 'POST':
        _, imap = get_email_connections(request)
        if not imap:
            text_to_speech("Session expired. Please log in again.")
            return JsonResponse({'result': 'logout'})

        try:
            # Select Gmail's Sent Mail folder
            imap.select('"[Gmail]/Sent Mail"')
            status, data = imap.search(None, 'ALL')

            if status != 'OK' or not data[0]:
                text_to_speech("Your sent folder is empty.")
                return JsonResponse({'result': 'success'})

            email_ids = data[0].split()
            top_email_ids = email_ids[-5:]  # get the latest 5
            top_email_ids.reverse()  # newest first

            from email.utils import parsedate_to_datetime

            for eid in top_email_ids:
                status, msg_data = imap.fetch(eid, '(RFC822)')
                if status != 'OK':
                    continue

                msg = email.message_from_bytes(msg_data[0][1])

                # Extract fields
                to_field = msg.get('to') or "Unknown recipient"
                subject = msg.get('subject') or "No subject"
                date_field = msg.get('date') or "Unknown date"

                # Format the date properly
                try:
                    parsed_date = parsedate_to_datetime(date_field)
                    formatted_date = parsed_date.strftime("%A, %d %B %Y at %I:%M %p")
                except Exception:
                    formatted_date = date_field

                # Announce details clearly
                text_to_speech(f"Email sent to {to_field}. Subject: {subject}. Sent on {formatted_date}.")

            text_to_speech("These were your five most recent sent emails.")

        except Exception as e:
            print(f"Error reading sent mail: {e}")
            text_to_speech("Could not access your sent folder.")
        finally:
            try:
                if imap:
                    imap.close()
                    imap.logout()
            except Exception:
                pass

        return JsonResponse({'result': 'success'})

    return render(request, 'homepage/sent.html')

def trash_view(request):
    """
    Voice-based Trash management:
      - Reads the top 5 latest emails from Trash
      - Asks user to 'restore' or 'permanently delete'
      - Performs the action on real mailbox
      - Always processes the latest 5 emails
    """
    if 'email_address' not in request.session:
        return redirect('login_view')

    if request.method == 'POST':
        _, imap = get_email_connections(request)
        if not imap:
            text_to_speech("Session expired. Please log in again.")
            return JsonResponse({'result': 'logout'})

        try:
            from email.utils import parsedate_to_datetime

            # Select Gmail Trash folder
            imap.select('"[Gmail]/Trash"')
            status, data = imap.search(None, 'ALL')

            if status != 'OK' or not data[0]:
                text_to_speech("Your trash folder is empty.")
                return JsonResponse({'result': 'success'})

            email_ids = data[0].split()
            top_email_ids = email_ids[-5:]  # latest 5 emails
            top_email_ids.reverse()  # newest first

            for eid in top_email_ids:
                # Fetch full email
                s, msg_data = imap.fetch(eid, '(RFC822)')
                if s != 'OK':
                    continue

                msg = email.message_from_bytes(msg_data[0][1])
                from_field = msg.get('from') or "Unknown sender"
                subject = msg.get('subject') or "No subject"
                date_field = msg.get('date') or "Unknown date"

                # Format date
                try:
                    parsed_date = parsedate_to_datetime(date_field)
                    formatted_date = parsed_date.strftime("%A, %d %B %Y at %I:%M %p")
                except Exception:
                    formatted_date = date_field

                # Announce email
                text_to_speech(f"Email from {from_field}. Subject: {subject}. Deleted on {formatted_date}.")
                text_to_speech("Say 'restore' to move this email back to inbox, 'permanent delete' to remove it forever, or 'menu' to go back.")

                user_choice = speech_to_text(6)
                if not user_choice:
                    text_to_speech("I did not catch that. Skipping this email.")
                    continue

                user_choice = user_choice.lower()

                # Restore
                if 'restore' in user_choice or 'move back' in user_choice:
                    try:
                        result = imap.copy(eid, "INBOX")
                        if result[0] == 'OK':
                            imap.store(eid, '+FLAGS', '\\Deleted')
                            text_to_speech("Email restored to inbox successfully.")
                        else:
                            text_to_speech("Could not restore this email.")
                    except Exception as restore_err:
                        print("Restore error:", restore_err)
                        text_to_speech("There was a problem restoring the email.")

                # Permanently delete
                elif 'permanent' in user_choice or 'delete' in user_choice:
                    try:
                        imap.store(eid, '+FLAGS', '\\Deleted')
                        text_to_speech("Email marked for permanent deletion.")
                    except Exception as del_err:
                        print("Permanent delete error:", del_err)
                        text_to_speech("Could not delete this email.")

                # Return to menu
                elif 'menu' in user_choice or 'back' in user_choice:
                    text_to_speech("Returning to main menu.")
                    break

                else:
                    text_to_speech("Invalid command. Skipping to next email.")

            # Commit deletions permanently
            imap.expunge()
            text_to_speech("Trash actions completed. Returning to main menu.")

        except Exception as e:
            print(f"Error accessing trash: {e}")
            text_to_speech("An error occurred while managing your trash folder.")
            return JsonResponse({'result': 'failure'})

        finally:
            try:
                imap.close()
                imap.logout()
            except Exception:
                pass

        return JsonResponse({'result': 'success'})

    return render(request, 'homepage/trash.html')

#helper functions for inbox_view

def extract_pdf_text(file_bytes):

    try:

        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))

        text = ""

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:

                text += page_text + "\n"

        return text

    except Exception as e:

        print("PDF error:", e)

        return None



def extract_txt_text(file_bytes):

    try:

        return file_bytes.decode("utf-8")

    except:

        return file_bytes.decode("latin-1")



def extract_docx_text(file_bytes):

    try:

        document = docx.Document(io.BytesIO(file_bytes))

        text = ""

        for para in document.paragraphs:

            text += para.text + "\n"

        return text

    except Exception as e:

        print("DOCX error:", e)

        return None



def handle_attachment(msg):

    for part in msg.walk():

        content_disposition = str(part.get("Content-Disposition"))

        if "attachment" in content_disposition:


            filename = part.get_filename()


            if not filename:

                continue


            text_to_speech(

                f"This email contains attachment {filename}. Say yes read to hear the attachment or say no."
            )


            choice = speech_to_text(5)


            if not choice or "yes" not in choice.lower():

                text_to_speech("Attachment skipped.")

                continue


            file_bytes = part.get_payload(decode=True)


            filename_lower = filename.lower()


            text = None


            if filename_lower.endswith(".pdf"):

                text = extract_pdf_text(file_bytes)


            elif filename_lower.endswith(".txt"):

                text = extract_txt_text(file_bytes)


            elif filename_lower.endswith(".docx"):

                text = extract_docx_text(file_bytes)


            else:

                text_to_speech("Unsupported attachment type.")

                return


            if text:

                text_to_speech("Reading attachment now.")

                _speak_chunks(text, 500)

            else:

                text_to_speech("Unable to read attachment.")

def inbox_view(request):

    if 'email_address' not in request.session:

        return redirect('login_view')


    if request.method == 'POST':

        try:


            text_to_speech(

                "Say unread to hear unread emails, search to find an email, or back to return to main menu."
            )


            action = speech_to_text(5)


            if not action:

                text_to_speech("I did not catch that.")

                return JsonResponse({'result': 'inbox'})


            action = action.lower()


            # ================= UNREAD =================


            if 'unread' in action:


                _, imap = get_email_connections(request)


                if not imap:

                    text_to_speech("Session expired.")

                    return JsonResponse({'result': 'logout'})


                try:


                    imap.select('INBOX')


                    status, data = imap.search(None, 'UNSEEN')


                    ids = data[0].split() if status == 'OK' else []


                    if not ids:


                        text_to_speech("No unread emails.")


                    else:


                        top_ids = ids[-5:]


                        for eid in reversed(top_ids):


                            s, msg_data = imap.fetch(eid, '(RFC822)')


                            if s != 'OK':

                                continue


                            msg = email.message_from_bytes(msg_data[0][1])


                            subject = msg.get('subject', "No subject")


                            from_field = msg.get('from', "Unknown sender")


                            date_field = msg.get('date', "Unknown date")


                            try:

                                from email.utils import parsedate_to_datetime

                                parsed_date = parsedate_to_datetime(date_field)

                                formatted_date = parsed_date.strftime(

                                    "%A, %d %B %Y at %I:%M %p"
                                )

                            except:

                                formatted_date = date_field


                            body = ""


                            if msg.is_multipart():

                                for part in msg.walk():

                                    content_type = part.get_content_type()

                                    content_disposition = str(part.get('Content-Disposition'))


                                    if content_type == 'text/plain' and 'attachment' not in content_disposition:


                                        charset = part.get_content_charset() or 'utf-8'


                                        body = part.get_payload(decode=True).decode(

                                            charset, errors='replace')

                                        break

                            else:


                                charset = msg.get_content_charset() or 'utf-8'


                                body = msg.get_payload(decode=True).decode(

                                    charset, errors='replace')


                            text_to_speech(f"From {from_field}")


                            text_to_speech(f"Received on {formatted_date}")


                            text_to_speech(f"Subject {subject}")


                            if body.strip():

                                text_to_speech("Email says")

                                _speak_chunks(body, 500)

                            else:

                                text_to_speech("No text content")


                            # ✅ ATTACHMENT READING FEATURE

                            handle_attachment(msg)


                            imap.store(eid, '+FLAGS', '\\Seen')


                        text_to_speech("Finished reading emails.")


                finally:


                    try:

                        imap.close()

                        imap.logout()

                    except:

                        pass


                return JsonResponse({'result': 'inbox'})


            # ================= BACK =================


            if 'back' in action:


                text_to_speech("Returning to main menu.")


                return JsonResponse({'result': 'options'})


            text_to_speech("Invalid option.")


            return JsonResponse({'result': 'inbox'})


        except Exception as e:


            print(e)


            text_to_speech("Error in inbox.")


            return JsonResponse({'result': 'inbox'})


    return render(request, 'homepage/inbox.html')

def delete_view(request):
    """
    Reads top 5 newest INBOX emails, announces details, asks for delete confirmation,
    moves selected emails to Bin/Trash in real mailbox, allows continue/menu.
    """
    if 'email_address' not in request.session:
        return redirect('login_view')

    if request.method == 'POST':
        _, imap = get_email_connections(request)
        if not imap:
            text_to_speech("Session expired. Please log in again.")
            return JsonResponse({'result': 'logout'})

        try:
            import email
            from email.utils import parsedate_to_datetime

            # Function to get current top 5 emails from INBOX
            def get_top_5_inbox_emails(imap_conn):
                imap_conn.select('INBOX')
                status, data = imap_conn.search(None, 'ALL')
                if status != 'OK' or not data[0]:
                    return []
                email_ids = data[0].split()
                top_email_ids = email_ids[-5:]  # latest 5
                top_email_ids.reverse()  # newest first
                return top_email_ids

            top_email_ids = get_top_5_inbox_emails(imap)
            if not top_email_ids:
                text_to_speech("Your inbox is empty. Nothing to delete.")
                return JsonResponse({'result': 'success'})

            for eid in top_email_ids:
                # Fetch full email (header + body)
                status, msg_data = imap.fetch(eid, '(RFC822)')
                if status != 'OK':
                    continue

                msg = email.message_from_bytes(msg_data[0][1])
                from_field = msg.get('from') or "Unknown sender"
                subject = msg.get('subject') or "No subject"
                date_field = msg.get('date') or "Unknown date"

                # Format date nicely
                try:
                    parsed_date = parsedate_to_datetime(date_field)
                    formatted_date = parsed_date.strftime("%A, %d %B %Y at %I:%M %p")
                except Exception:
                    formatted_date = date_field

                # Announce email details
                text_to_speech(f"Email from {from_field}. Subject: {subject}. Received on {formatted_date}.")
                text_to_speech("Do you want to delete this email? Say yes delete or no delete")

                response = speech_to_text(5)
                if response and "yes" in response.lower() and "delete" in response.lower():
                    try:
                        # Move email from INBOX → Bin/Trash
                        result = imap.copy(eid, "[Gmail]/Trash")  # Gmail
                        if result[0] != "OK":
                            imap.copy(eid, "Trash")  # Outlook/Yahoo fallback

                        # Mark original INBOX email as deleted
                        imap.store(eid, '+FLAGS', '\\Deleted')
                        text_to_speech("Email moved to bin successfully.")
                    except Exception as copy_err:
                        print("Error moving to bin:", copy_err)
                        text_to_speech("Could not move this email to bin. Skipping.")
                else:
                    # Any response that is not "yes delete" is treated as keep
                    text_to_speech("Email kept safely.")


                # Ask user whether to continue deleting or return to menu
                text_to_speech("Do you want to continue deleting other emails, or go back to the menu?")
                next_action = speech_to_text(5)
                if next_action and "menu" in next_action.lower():
                    text_to_speech("Returning to main menu.")
                    break
                elif not next_action or "continue" not in next_action.lower():
                    text_to_speech("No valid response. Returning to main menu.")
                    break

            # Commit deletions in INBOX (actually removes emails)
            imap.expunge()
            text_to_speech("Selected emails have been moved to bin in your inbox.")

        except Exception as e:
            print(f"Error deleting emails: {e}")
            text_to_speech("An error occurred while moving emails to bin.")
            return JsonResponse({'result': 'failure'})

        finally:
            try:
                imap.close()
                imap.logout()
            except Exception:
                pass

        return JsonResponse({'result': 'success'})

    return render(request, 'homepage/delete.html')

def label_view(request):

    """
    Voice based Label Management
    Features:
    - Create Label
    - List Labels
    - Move Email to Label
    - Read Emails from Label
    - Back to menu
    """

    if 'email_address' not in request.session:

        text_to_speech("Session expired. Please login again.")

        return redirect('homepage:login')


    if request.method == 'POST':

        try:

            text_to_speech(
                "Label menu. "
                "Say create to create label. "
                "Say list to hear labels. "
                "Say move to move latest unread email. "
                "Say read to read label emails. "
                "Or say back to return."
            )


            action = speech_to_text(5)


            if not action:

                text_to_speech("No command detected.")

                return JsonResponse({'result': 'label'})


            action = action.lower()


            smtp, imap = get_email_connections(request)


            if not imap:

                text_to_speech("Connection failed.")

                return JsonResponse({'result': 'logout'})


            # ===============================
            # CREATE LABEL
            # ===============================

            if "create" in action:

                text_to_speech("Say label name")

                label_name = speech_to_text(5)

                if label_name:

                    label_name = label_name.strip()

                    # ✅ FIX: ADD QUOTES
                    label_name = f'"{label_name}"'

                    print("Creating label:", label_name)

                    status, response = imap.create(label_name)

                    print("CREATE STATUS:", status, response)

                    if status == 'OK':

                        text_to_speech(f"Label created successfully")

                    else:

                        text_to_speech("Label already exists or cannot create")

                else:

                    text_to_speech("Label name not detected")

                imap.logout()

                return JsonResponse({'result': 'label'})


            # ===============================
            # LIST LABELS
            # ===============================

            elif "list" in action:

                status, labels = imap.list()

                if status == 'OK':

                    text_to_speech("Your labels are")

                    for label in labels:

                        label_name = label.decode().split(' "/" ')[-1]

                        text_to_speech(label_name)

                else:

                    text_to_speech("Unable to fetch labels")


                imap.logout()

                return JsonResponse({'result': 'label'})


            # ===============================
            # MOVE EMAIL
            # ===============================

            elif "move" in action:


                imap.select("INBOX")

                status, messages = imap.search(None, 'UNSEEN')


                mail_ids = messages[0].split()


                if not mail_ids:

                    text_to_speech("No unread emails")

                    imap.logout()

                    return JsonResponse({'result': 'label'})


                latest = mail_ids[-1]


                text_to_speech("Say label name")

                label_name = speech_to_text(5)


                if not label_name:

                    text_to_speech("Label name not detected")

                    imap.logout()

                    return JsonResponse({'result': 'label'})


                label_name = label_name.strip()


                copy_status = imap.copy(latest, label_name)


                if copy_status[0] == 'OK':

                    imap.store(latest, '+FLAGS', '\\Deleted')

                    imap.expunge()

                    text_to_speech("Email moved successfully")

                else:

                    text_to_speech("Label not found. Please create label first")


                imap.logout()

                return JsonResponse({'result': 'label'})



            # ===============================
            # READ LABEL EMAIL
            # ===============================

            elif "read" in action:


                text_to_speech("Say label name")

                label_name = speech_to_text(5)


                if not label_name:

                    text_to_speech("Label name not detected")

                    imap.logout()

                    return JsonResponse({'result': 'label'})


                label_name = label_name.strip()


                status, messages = imap.select(label_name)


                if status != 'OK':

                    text_to_speech("Label not found")

                    imap.logout()

                    return JsonResponse({'result': 'label'})


                status, data = imap.search(None, 'ALL')


                mail_ids = data[0].split()


                if not mail_ids:

                    text_to_speech("No emails in this label")

                    imap.logout()

                    return JsonResponse({'result': 'label'})


                latest = mail_ids[-1]


                status, msg_data = imap.fetch(latest, '(RFC822)')


                msg = email.message_from_bytes(msg_data[0][1])


                subject = msg["subject"]

                sender = msg["from"]


                text_to_speech(f"Email from {sender}")

                text_to_speech(f"Subject is {subject}")


                imap.logout()

                return JsonResponse({'result': 'label'})



            # ===============================
            # BACK
            # ===============================

            elif "back" in action:


                text_to_speech("Returning to menu")

                imap.logout()

                return JsonResponse({'result': 'options'})



            else:

                text_to_speech("Invalid option")

                imap.logout()

                return JsonResponse({'result': 'label'})



        except Exception as e:


            print("Label error:", e)

            text_to_speech("Error in label section")

            return JsonResponse({'result': 'label'})


    return render(request, 'homepage/label.html')

def move_email_to_label(imap, label_name, email_id):

    try:

        # Copy email to label
        imap.copy(email_id, label_name)

        # Delete from inbox
        imap.store(email_id, '+FLAGS', '\\Deleted')

        imap.expunge()

        return True

    except Exception as e:

        print("Move Error:", e)

        return False