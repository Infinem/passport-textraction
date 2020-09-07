import datetime
from mrz.checker.td3 import TD3CodeChecker

from app.global_variables import alphabet_dict

def clear_first_row(first_row):
    first_row = first_row.upper()
    first_row = [string for string in first_row.split('<') 
                if string not in ['', ' ', 'K', 'KK', 'KKK', 'KKKK', 'KKKKK', '.', ',']]
    if first_row[0][0] == 'P' and len(first_row) < 3:
        split_str = 'UZB' + first_row[0][5:]
        first_row.pop(0)
        first_row.insert(0, split_str)
        first_row.insert(0, 'P')
    first_row = [string for string in first_row if ' ' not in string]
    new_first_row = []
    for item in first_row:
        for c in range(len(item)):
            if not item[c].isalpha():
                if item[:c] == '':
                    break
                else:
                    new_first_row.append(item[:c])
                    break
        else:
            new_first_row.append(item)
    return new_first_row

def clear_second_row(second_row):
    second_row = second_row.upper()
    second_row = second_row.replace(' ', '')
    idx_list = [10, 11, 12]
    if len(second_row) != 44:
        for i in range(len(second_row)):
            if second_row[i].isalpha() and i in idx_list:
                pos_list = []
                for j in idx_list:
                    if second_row[j].isalpha():
                        pos_list.append(j)
        first_part = second_row[:pos_list[0]]
        second_part = second_row[pos_list[::-1][0]+1:]
    else:
        first_part = second_row[:10]
        second_part = second_row[13:]
    second_row = first_part + 'UZB' + second_part
    return second_row

def pad_first_row(first_row):
    padded_row = ''
    for item in first_row:
        if len(item) == 1:
            padded_row += item + '<'
        if len(item) >= 2:
            padded_row += item + '<<'
    while len(padded_row) < 44:
        padded_row += '<'
    return padded_row

def check_field(check_digit, **kwargs):
    sum_value = 0
    for k, v in kwargs.items():
        weights = ([7, 3, 1] * int((len(v) / 3) + 1))
        for i in range(len(v)):
            if v[i].isalpha():
                for key, value in alphabet_dict.items():
                    if v[i] == key:
                        sum_value += value * weights[i]
            else:
                sum_value += int(v[i]) * weights[i]
    if sum_value % 10 == int(check_digit):
        if len(kwargs) == 1:
            values_list = list(kwargs.values())[0]
        else:
            values_list = list(kwargs.values())
    else:
        if len(kwargs) == 1:
            values_list = False
        else:
            values_list = [False for v in list(kwargs.items())]
    return values_list

def convert_date(any_date):
    if int(any_date[:2]) <= int(datetime.date.today().strftime("%Y")[2:]) + 10:
        any_date = f'{datetime.date.today().strftime("%Y")[:2]}{any_date}'
    else:
        any_date = f'19{any_date}'
    return datetime.datetime.strptime(any_date, '%Y%m%d').strftime('%d.%m.%Y')

def validate_whole(text):
    td3_check = TD3CodeChecker(text, check_expiry=True) 
    if td3_check:
        fields = td3_check.fields()
        if fields.document_type == 'P':
            document_type = 'Passport'
        if fields.sex == 'M':
            sex = 'Male'
        else:
            sex = 'Female'
        json_object = {
                'Document Type': document_type,
                'Issuing Country': fields.country,
                'Surname': fields.surname,
                'Name': fields.name,
                'Passport Number': fields.document_number,
                'Nationality': fields.nationality,
                'Date Of Birth': convert_date(fields.birth_date),
                'Sex': sex,
                'Date Of Expiry': convert_date(fields.expiry_date),
                'Personal Number': fields.optional_data,
                }
        return json_object
    else:
        return False

def add_validated(text):
    rows = text.split('\n')
    rows[0] = [string for string in rows[0].split('<') if string not in ['', ' ']]
    json_object = {}
    if rows[0][0] == 'P':
        document_type = 'Passport'
        json_object = {'Document Type': document_type}
    if rows[0][1][:3] == 'UZB':
        country = 'UZB'
        json_object = {**json_object, 'Issuing Country': country}
    surname = rows[0][1][3:]
    json_object = {**json_object, 'Surname': surname}
    name = rows[0][2]
    json_object = {**json_object, 'Name': name}
    document_number = check_field(check_digit=rows[1][9], document_number=rows[1][:9])
    if document_number:
        json_object = {**json_object, 'Passport Number': document_number}
    nationality = rows[1][10:13]
    json_object = {**json_object, 'Nationality': nationality}
    birth_date = check_field(check_digit=rows[1][19], birth_date=rows[1][13:19])
    if birth_date:
         json_object = {**json_object, 'Date Of Birth': convert_date(birth_date)}
    if rows[1][20] == 'M':
        sex = 'Male'
    else:
        sex = 'Female'
    json_object = {**json_object, 'Sex': sex}
    expiry_date = check_field(check_digit=rows[1][27], expiry_date=rows[1][21:27])
    if expiry_date:
        json_object = {**json_object, 'Date Of Expiry': convert_date(expiry_date)}
    personal_number = check_field(check_digit=rows[1][42], personal_number=rows[1][28:42])
    if personal_number:
        json_object = {**json_object, 'Personal Number': personal_number}
    if json_object:
        return json_object
    else:
        json_object = {'Error': 'Validation failed!'}
        return json_object

def parse(text):
    if '\n' in text:
        rows = text.split('\n')
    else:
        rows = text.split(' ')
    rows[0] = clear_first_row(rows[0])
    rows[0] = pad_first_row(rows[0])
    rows[1] = clear_second_row(rows[1])
    json_object = validate_whole(rows[0] + '\n' + rows[1])
    if not json_object:
        json_object = add_validated(rows[0] + '\n' + rows[1])  
    return json_object