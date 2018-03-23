from flask import Flask, render_template, redirect, request, session, flash

import logging
from logging import FileHandler

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders

import re

import stripe

from fpdf import FPDF

import random

import string

import os, sys

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9\.\+_-]+@[a-zA-Z0-9\._-]+\.[a-zA-Z]*$')

app = Flask(__name__)

app.secret_key = 'FitgeekSuperSecret'

file_handler = FileHandler("debug.log","a")
file_handler.setLevel(logging.WARNING)
app.logger.addHandler(file_handler)

@app.route('/')
def index():
	session.clear()
	return render_template('index.html')

@app.route('/our_store')
def our_store():
	return render_template('our-store.html')

@app.route('/gait_analysis')
def gait_analysis():
	return render_template('gait_analysis.html')

#alternative gait analysis routes from old website
@app.route('/gait-analysis/')
def gait_analysis_slash():
	return redirect('/gait_analysis')

@app.route('/gait-analysis')
def gait_analysis_no_slash():
	return redirect('/gait_analysis')

@app.route('/GaitAnalysis')
def GaitAnalysis():
	return redirect('/gait_analysis')

@app.route('/GaitAnalysis/')
def GaitAnalysis_slash():
	return redirect('/gait_analysis')

@app.route('/about')
def about():
	return render_template('about.html')

@app.route('/about/')
def about_slash():
	return redirect('/about')

# who we are routes from old website redirected to about
@app.route('/who-we-are/')
def who_we_are_slash():
	return redirect('/about#who-we-are')

@app.route('/contact')
def contact():
	return render_template('contact.html')

@app.route('/contact/')
def contact_slash():
	return redirect('/contact')

@app.route('/hours-and-directions/')
def hours_and_directions():
	return redirect("/#hours_and_directions")

#running shoe route from old website redirected home
@app.route('/running-shoes/')
def running_shoes():
	return redirect("/")

@app.route('/processMessage', methods=['POST'])
def processMessage():

	# Validate form - although there is front end validation, the following is just in case front end validation fails
	# i.e., user deleted code from browser or browser does not support front end validation
	validMessage = True
	if request.form['name'] == "":
		flash("Please enter a name", 'invalid_message')
		validMessage = False
	if request.form['subject'] == "":
		flash("Please enter a subject", 'invalid_message')
		validMessage = False
	if request.form['message'] == "":
		flash("Please enter a message", 'invalid_message')
		validMessage = False
	if request.form['email'] == "" or not EMAIL_REGEX.match(request.form['email']):
		flash("Please enter a valid email address", 'invalid_message')
		validMessage = False

	#if validation passes, send message
	if validMessage == True:
		fromAddress = request.form['email']
		toAddress = 'info@fitgeeksports.com'
		msg = MIMEMultipart()
		msg['From'] = fromAddress
		msg['To'] = toAddress
		msg['Subject'] = "Email contact through Fitgeek Website.  Sender Name: "+request.form['name']+" | Email: "+fromAddress+" | Subject: " + request.form['subject']

		body = request.form['message']
		msg.attach(MIMEText(body, 'plain'))

		mail = smtplib.SMTP('smtp.gmail.com', 587)
		mail.starttls()
		mail.login('staff@fitgeeksports.com', 'bfxnchurfsmpysmc')
		text = msg.as_string()
		mail.sendmail(fromAddress, toAddress, text)
		mail.quit()
		flash("Your message has been sent. Thanks!", 'valid_message')
	return redirect("/contact")

@app.route('/gift_cards')
def gift_cards():
	session.clear()
	return render_template('gift_cards.html')

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():

	# Validate form - although there is front end validation, the following is just in case front end validation fails
	# i.e., user deleted code from browser or browser does not support front end validation
	validForm = True
	if request.form['recipient_name'] == "":
		flash("Please enter the recipient's name", 'invalid_message')
		validForm = False
	if request.form['recipient_email'] == "" or not EMAIL_REGEX.match(request.form['recipient_email']):
		flash("Please enter a valid recipient's email", 'invalid_message')
		validForm = False
	if request.form['giver_name'] == "":
		flash("Please enter your name", 'invalid_message')
		validForm = False
	if request.form['giver_email'] == "" or not EMAIL_REGEX.match(request.form['giver_email']):
		flash("Please enter a valid email for your email", 'invalid_message')
		validForm = False
	if request.form['gift_amount'] == "":
		flash("Please enter a gift amount", 'invalid_message')
		validForm = False

	#check if the amount is in the correct format
	try:
		if ( float(request.form['gift_amount']) % 1 != 0) or ( float(request.form['gift_amount']) < 1):
			flash("Please enter a gift amount that is a whole number (i.e., no cents) greater than $1", 'invalid_message')
			validForm = False
	except:
		flash("Please enter a gift amount that is a whole number (i.e., no cents) greater than $1", 'invalid_message')
		validForm = False

	#if validation passes, then store information in session and redirect to checkout form
	if validForm == True:
		session['gift_certificate_details'] = {
			'recipient_name': request.form['recipient_name'],
			'recipient_email': request.form['recipient_email'],
			'giver_name': request.form['giver_name'],
			'giver_email': request.form['giver_email'],
			'gift_amount': int(float(request.form['gift_amount']))
		}
		if len(request.form['message']) > 0:
			session['gift_certificate_details']['message'] = request.form['message']
		return redirect("/checkout")

	#if validation fails, redirect to gift certifacates page with flashed error messages
	return redirect("/gift_cards#gift_certificate_form")

@app.route('/clear_cart')
def clear_cart():
	session.pop('gift_certificate_details')
	return redirect('/checkout')

@app.route('/checkout')
def checkout():
	return render_template('checkout.html')

@app.route('/process_stripe', methods=['POST'])
def process_stripe():
	gift_amount_in_pennies = session['gift_certificate_details']['gift_amount'] * 100

	gift_description = "Gift certificate purchase from " + session['gift_certificate_details']['giver_name'] + " (" + session['gift_certificate_details']['giver_email'] + ") to " + session['gift_certificate_details']['recipient_name'] + " (" + session['gift_certificate_details']['recipient_email'] + ")"

	# stripe key for testing
	# stripe.api_key = *** REMOVED ***

	#stripe key for live
	stripe.api_key = # *** REMOVED ***

	# Get the credit card details submitted by the form
	token = request.form['stripeToken']

	# Create the charge on Stripe's servers - this will charge the user's card
	error = False
	try:
		charge = stripe.Charge.create(
			amount=gift_amount_in_pennies, # amount in cents
			currency="usd",
			source=token,
			description=gift_description
		)
	except stripe.error.CardError, e:
	  # The card has been declined.  Flash error message
		error = True
		flash("Error processing your card.  Your card has not been charged.  Please try again.", 'processing_error_message')
		pass
	#if no processing error, generate PDF gift certificate and email to sender and recipient
	#if there is a processing error, simply return to checkout page and flash message
	if error == False:

		# Generate list of certificate numbers to check if certificate number already exists
		path = "./gift_certificates/pdf_certificates"
		certificate_nums = os.listdir(path)
		length = len(certificate_nums)
		index = 0
		while index < length:
			#remove hidden files
			if certificate_nums[index].startswith('.'):
				del certificate_nums[index]
				length -= 1
			else:
				#remove ".pdf" from file names
				certificate_nums[index] = certificate_nums[index][:8]
				index += 1

		# generate random 8-characer code
		certificate_number = ""
		for i in range(0,8):
			rand_char = random.choice( string.ascii_uppercase + string.digits )
			certificate_number += rand_char

		# keep generating new 8-character code until there is a unique one
		while certificate_number in certificate_nums:
			certificate_number = ""
			for i in range(0,8):
				rand_char = random.choice( string.ascii_uppercase + string.digits )
				certificate_number += rand_char

		#create certificate object
		pdf_certificate = FPDF(format="letter")
		pdf_certificate.add_page()
		pdf_certificate.set_font('Times', 'B', 14)
		#for localhost version:
		#pdf_certificate.image('/Users/Wing/Desktop/New_Fitgeek_Website/gift_certificates/blank_certificate/fitgeek_gift_certificate.jpg', 15, 15, 185)
		# pdf_certificate.image('/home/fg_admin/fitgeek_website/gift_certificates/blank_certificate/fitgeek_gift_certificate.jpg', 15, 15, 185)
		pdf_certificate.image('./gift_certificates/blank_certificate/fitgeek_gift_certificate.jpg', 15, 15, 185)
		pdf_certificate.text(60, 65, "From:   " + session['gift_certificate_details']['giver_name'])
		pdf_certificate.text(60, 75, "To:   " + session['gift_certificate_details']['recipient_name'])
		pdf_certificate.text(60, 85, "Amount:   $ " + str(session['gift_certificate_details']['gift_amount']))
		pdf_certificate.text(60, 95, "Certificate Number:   " + certificate_number)
		pdf_certificate.text(20, 130, "To redeem, come into Fitgeek Sports and show this certificate (either printed")
		pdf_certificate.text(20, 140, "or on your phone) at checkout.")
		pdf_certificate.text(20, 150, "Fitgeek Sports is located at:")
		pdf_certificate.text(40, 160, "21000 Stevens Creek Blvd., Cupertino, CA 95014")
		pdf_certificate.text(40, 167, "Phone: 408-218-2088 | Website: www.fitgeeksports.com")
		pdf_certificate.text(20, 180, "See you soon!")
		certificate_filename = certificate_number + ".pdf"
		#pdf_certificate.output('/Users/Wing/Desktop/New_Fitgeek_Website/gift_certificates/pdf_certificates/' + certificate_filename, 'F')
		# pdf_certificate.output('/home/fg_admin/fitgeek_website/gift_certificates/pdf_certificates/' + certificate_filename, 'F')
		pdf_certificate.output('./gift_certificates/pdf_certificates/' + certificate_filename, 'F')
		#save certificate number in session - same as order number
		session['gift_certificate_number'] = certificate_number

		#email certificate to receipient, and copy Fitgeek
		fromaddr = "staff@fitgeeksports.com"
		toaddr = session['gift_certificate_details']['recipient_email']
		bcc = ['info@fitgeeksports.com', 'wing@fitgeeksports.com']
		all_addrs = [toaddr] + bcc
		recipient_msg = MIMEMultipart()
		recipient_msg['From'] = fromaddr
		recipient_msg['To'] = toaddr
		recipient_msg['Subject'] = session['gift_certificate_details']['giver_name'] + " has sent you a $" + str(session['gift_certificate_details']['gift_amount']) + " gift certificate to Fitgeek Sports!"
		body = "Dear " + session['gift_certificate_details']['recipient_name'] +",\n\n" + \
			session['gift_certificate_details']['giver_name'] + " (" + session['gift_certificate_details']['giver_email'] + ") has sent you a $" + str(session['gift_certificate_details']['gift_amount']) + " gift certificate to Fitgeek Sports!\n\n"
		if 'message' in session['gift_certificate_details']:
			body += "Message from " + session['gift_certificate_details']['giver_name'] + ":\n" + session['gift_certificate_details']['message'] + "\n\n"
		body += "Gift Certificate Number: " + certificate_number + "\n\nTo redeem your gift certificate, come into Fitgeek Sports at 21000 Stevens Creek Blvd., Cupertino, CA 95014, and show this certificate (either printed or on your phone) at checkout.\n\nSee you soon!\n\nFitgeek Sports"
		recipient_msg.attach(MIMEText(body, 'plain'))
		filename = certificate_filename
		#attachment = open("/Users/Wing/Desktop/New_Fitgeek_Website/gift_certificates/pdf_certificates/" + certificate_filename, "rb")
		# attachment = open("/home/fg_admin/fitgeek_website/gift_certificates/pdf_certificates/" + certificate_filename, "rb")
		attachment = open("./gift_certificates/pdf_certificates/" + certificate_filename, "rb")
		part = MIMEBase('application', 'octet-stream')
		part.set_payload((attachment).read())
		encoders.encode_base64(part)
		part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
		recipient_msg.attach(part)
		server = smtplib.SMTP('smtp.gmail.com', 587)
		server.starttls()
		server.login(fromaddr, "bfxnchurfsmpysmc")
		text = recipient_msg.as_string()
		server.sendmail(fromaddr, all_addrs, text)
		server.quit()

		#email certificate to sender, and copy Fitgeek
		fromaddr = "staff@fitgeeksports.com"
		toaddr = session['gift_certificate_details']['giver_email']
		bcc = ['info@fitgeeksports.com', 'wing@fitgeeksports.com']
		all_addrs = [toaddr] + bcc
		recipient_msg = MIMEMultipart()
		recipient_msg['From'] = fromaddr
		recipient_msg['To'] = toaddr
		recipient_msg['Subject'] = "Order Confirmation - Reference No.: " + certificate_number
		body = "Dear " + session['gift_certificate_details']['giver_name'] +",\n\n" + \
			"Thank you for your gift certificate order! Your gift certificate of $" + str(session['gift_certificate_details']['gift_amount']) + \
			" has been sent to " + session['gift_certificate_details']['recipient_name'] + " at the email " + session['gift_certificate_details']['recipient_email'] + ".\n\n" + \
			"If you have any questions about your order, don't hesistate to email us at info@fitgeeksports.com.\n\nBest Regards,\n\nFitgeek Sports"
		recipient_msg.attach(MIMEText(body, 'plain'))
		server = smtplib.SMTP('smtp.gmail.com', 587)
		server.starttls()
		server.login(fromaddr, "bfxnchurfsmpysmc")
		text = recipient_msg.as_string()
		server.sendmail(fromaddr, all_addrs, text)
		server.quit()

		return redirect('/order_complete')
	return redirect('/checkout')

@app.route('/order_complete')
def order_complete():
	return render_template('order_complete.html')

@app.route('/privacy_policy')
def privacy_policy():
	return render_template('privacy_policy.html')

@app.route('/faq')
def faq():
	return render_template('FAQs.html')

@app.route('/all-about-insoles/')
def all_bout_insoles():
	return render_template('all_about_insoles.html')

@app.route('/what-is-my-foot-type/')
def what_is_my_foot_type():
	return render_template('foot_types.html')

@app.route('/types-of-running-shoes/')
def types_of_running_shoes():
	return render_template('running_shoes_types.html')

@app.route('/six-tips-when-looking-for-walking-shoes/')
def six_tips_when_looking_for_walking_shoes():
	return render_template('picking_walking_shoes.html')

@app.route('/popular-running-styles/')
def popular_running_styles():
	return render_template('running_styles.html')

@app.route('/common-running-injuries/')
def common_running_injuries():
	return render_template('running_injuries.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == "__main__":
	app.run(debug=True, host='0.0.0.0')
