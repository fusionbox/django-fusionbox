import phonenumbers

def format_phonenumber(number, region):
    """
    Format a phonenumber for dialing from the specified region.
    Regions can be: "US", "JP", "FR", ...
    """
    region = region.upper()
    n = phonenumbers.parse(number, region)

    if phonenumbers.region_code_for_number(n) == region:
        formatting = phonenumbers.PhoneNumberFormat.NATIONAL
    else:
        formatting = phonenumbers.PhoneNumberFormat.INTERNATIONAL
    return phonenumbers.format_number(n, formatting)

def format_us_phonenumber(number):
    """
    Format a phonenumber for dialing from the US
    """
    return format_phonenumber(number, "US")
