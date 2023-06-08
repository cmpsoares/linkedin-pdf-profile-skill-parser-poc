import PyPDF2
import pikepdf
from datetime import datetime
import json
import re

def extract_text_from_pdf(file_path):
    # Open the PDF file in read-binary mode
    with open(file_path, 'rb') as file:
        # Create a PDF file reader object
        reader = PyPDF2.PdfReader(file)

        # Initialize an empty string to hold the extracted text
        extracted_text = ''

        # Loop through each page and extract the text
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            # Add page's text (except the last line which is the pages string) to the total text
            extracted_text += page.extract_text().rsplit('\n', 1)[0]
    return extracted_text

def filter_and_clean_urls(lst):
    # Initialize an empty list to hold the cleaned URLs
    cleaned_urls = []

    # Loop through each string in the list
    for s in lst:
        # Split the string into words
        words = s.split()

        # Loop through each word
        for word in words:
            # If the word contains a '.' and no whitespace, it's a URL
            if '.' in word and not ' ' in word:
                cleaned_urls.append(word)

    return cleaned_urls

def extract_data_from_text(text, NAME=None, TITLE=None, ADDRESS=None, PHONE=None, EMAIL=None):
    # Initialize the variables
    name = NAME
    title = TITLE
    address = ADDRESS
    phones = []
    emails = []
    urls = []
    top_skills = []
    languages = {}
    summary = ''
    experiences_lines = []
    experiences = []
    education = []
    shool_line = True

    # Add the phone number and email to the lists
    if PHONE is not None:
        phones.append(PHONE)
    if EMAIL is not None:
        emails.append(EMAIL)

    # Split the text into lines
    lines = text.split('\n')

    # initialize the variables where the specific lines start
    contact_line = email_line = urls_line = top_skills_line = languages_line = certifications_line = summary_line = experience_line = education_line = len(lines)

    # Iterate through each line and extract the data
    for i in range(len(lines)):
        if "Contact" in lines[i]:
            contact_line = i
        if (i > contact_line) & (i < email_line) & ("@" not in lines[i]) & ("Contact" not in lines[i]):
            phones.append(lines[i])
        if "@" in lines[i]:
            email_line = i
        if (i >= email_line) & (i < urls_line) & ("www.linkedin.com" not in lines[i]):
            emails.append(lines[i])
        if "www.linkedin.com" in lines[i]:
            urls_line = i
        if (i >= urls_line) & (i < top_skills_line) & ("Top Skills" not in lines[i]):
            urls.append(lines[i])
        if "Top Skills" in lines[i]:
            top_skills_line = i
        if (i > top_skills_line) & (i < languages_line) & ("Languages" not in lines[i]):
            top_skills.append(lines[i])
        if "Languages" in lines[i]:
            languages_line = i
        if (i > languages_line) & (i < certifications_line) & ("Certifications" not in lines[i]):
            language = lines[i].split('(')[0].strip()
            proficiency = lines[i].rsplit('(')[1].rstrip(")").strip()
            languages[language] = proficiency
        if "Certifications" in lines[i]:
            certifications_line = i
        if "Summary" in lines[i]:
            summary_line = i
            if name is None:
                name = lines[i-3]
            if title is None:
                title = lines[i-2]
            if address is None:
                address = lines[i-1]
        if (i > summary_line) & (i < experience_line) & ("Experience" not in lines[i]):
            summary += lines[i] + ' '
        if "Experience" in lines[i]:
            experience_line = i
        if (i > experience_line) & ("year" in lines[i] or "month" in lines[i] or "day" in lines[i]) & ("Education" not in lines[i]):
            experiences_lines.append(i-2)
        if "Education" in lines[i]:
            education_line = i
        if (i > education_line):
            if shool_line:
                school = lines[i]
                shool_line = False
            else:
                degree = lines[i].replace('\xa0', ' ').split('· (')[0].strip()
                attendance = lines[i].replace('\xa0', ' ').split('· (')[-1].rstrip(')').strip()
                education.append({
                        'school': school,
                        'degree': degree,
                        'attendance': {
                            'text': attendance,
                            'start': attendance.split('-')[0].strip(),
                            'end': attendance.split('-')[-1].strip(),
                        },
                    })
                shool_line = True

    print(experiences_lines)

    # Second iteration to extract the experience
    experiences_lines.append(education_line)
    for i in range(len(experiences_lines)):
        if i != len(experiences_lines)-1:
            company = lines[experiences_lines[i]].replace('\xa0', ' ')
            title = lines[experiences_lines[i]+1].replace('\xa0', ' ')
            dates = lines[experiences_lines[i]+2].replace('\xa0', ' ')
            location = lines[experiences_lines[i]+3].replace('\xa0', ' ')
            description = ' '.join(lines[experiences_lines[i]+4:experiences_lines[i+1]]).replace('\xa0', ' ')
            start_date = dates.split('-')[0].strip()
            end_date = dates.split('-')[-1].split('(')[0].strip()
            if end_date == 'Present':
                end_date = datetime.now().strftime('%b %Y')
            pattern = r'\((.*?)\)'
            durations = re.findall(pattern, dates)
            # If a duration was found, print it
            if durations:
                duration = durations[0].strip()
            else:
                duration = '0 years'
            experiences.append({
                    'company': company,
                    'title': title,
                    'dates': {
                        'text': dates,
                        'start': start_date,
                        'end': end_date,
                        'duration': duration,
                        'present': 'Present' in dates,
                        },
                    'location': location,
                    'description': description,
                })

    # Return the contact info as a dictionary
    return {
        'name': name.strip(),
        'title': title.strip(),
        'contacts': {
            'address': address.strip(),
            'phone': phones,
            'email': emails,
            'urls': filter_and_clean_urls(urls),
            },
        'summary': summary.strip(),
        'skills': {
            'top_skills': top_skills,
            'languages': languages,
            'certifications': '',
            'education': education,
            'skills': {
                'technologies': '',
                'industry': '',
                'other': '',
            },
        },
        'experience': experiences,
    }
    

def extract_metadata_from_pdf(file_path):
    # Initialize an empty dictionary
    data = {}

    # Open PDF with pikepdf
    pdf = pikepdf.Pdf.open(file_path)

    # Extract metadata from PDF
    pdf_info = pdf.docinfo

    # Print out the metadata
    for key, value in pdf_info.items():
        value = str(value)
        if key == '/CreationDate':
            key2 = 'creation_date'
            date_format = 'd:%Y%m%d%H%M%Sz'
            date_obj = datetime.strptime(value, date_format)
            value = date_obj.strftime('%Y-%m-%d %H:%M:%S')
        elif key == '/Producer':
            key2 = 'producer'
        elif key == '/Creator':
            key2 = 'creator'
        elif key == '/Title':
            key2 = 'title'
        elif key == '/Author':
            key2 = 'author'
        elif key == '/Subject':
            key2 = 'subject'
        else:
            key2 = key
        data[key2] = value

    # Close the PDF file object
    pdf.close()

    return data

def save_data_as_json(data, output_path):
    # Convert the dictionary to JSON string
    json_string = json.dumps(data)

    # Write to JSON file
    with open(output_path, 'w') as f:
        f.write(json_string)
    
    f.close()

# Usage
FILE = 'examples/Profile.pdf'
OUTPUT = 'examples/data.json'
NAME = 'Carlos Manuel Soares'

extracted_text = extract_text_from_pdf(FILE)
#print(extracted_text)
#print('\n========================================\n')

extracted_data = extract_data_from_text(extracted_text, NAME=NAME, TITLE=None, ADDRESS=None, PHONE='+351 969 571 027', EMAIL=None)
#print(extracted_data)

metadata = extract_metadata_from_pdf(FILE)
#print(metadata)

# Create final dictionary
json_data = {
    'metadata' : metadata,
    'data' : extracted_data
    }
save_data_as_json(json_data, OUTPUT)
#print(json_data)