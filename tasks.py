from robocorp.tasks import task
from robocorp import browser
from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive

@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    # browser.configure(
    #     slowmo=500,
    #     headless=True,
    # )
    open_robot_order_website()
    go_to_order_tab()
    orders = get_orders()
    for row in orders:
       close_annoying_modal()
       fill_the_form(row)
    archive_receipts()
    

def open_robot_order_website():
    """
        Access to web site to request a robot
    """
    browser.goto("https://robotsparebinindustries.com/")

def go_to_order_tab():
    """
        Access to web section to request a robot
    """
    page = browser.page()
    page.click("text=Order your robot!")

def get_orders():
    """
        Get robot order data from order.csv
    """
    http = HTTP()
    http.download(url="https://robotsparebinindustries.com/orders.csv", overwrite=True)

    tables = Tables()
    orders = tables.read_table_from_csv(
        path="orders.csv", 
        columns=["Order number", "Head", "Body", "Legs", "Address"]
    )
    return orders

def close_annoying_modal():
    """
        Close annoying modal before fill the form
    """
    page = browser.page()
    page.click("text=Ok")

def body_selector(body_id):
    """
        Build the id selector for the radio button to use
    """
    return "id-body-" + body_id

def fill_the_form(row):
    """
        Fill the form
        Validate if the server is active
    """
    page = browser.page()
    page.select_option("#head", str(row["Head"]))
    page.click("id="+body_selector(str(row["Body"])))
    page.get_by_placeholder("Enter the part number for the legs").fill(row["Legs"])
    page.fill("#address", str(row["Address"]))
    page.click("text=preview")
    page.click("#order")
    if page.get_by_role("alert").locator(".alert .alert-danger").is_hidden():
        is_complete = store_receipt_as_pdf(str(row["Order number"]))
        if is_complete == 0:
            page.click("#order-another")
        else :
            fill_the_form(row)
    else:
        fill_the_form(row)

def store_receipt_as_pdf(order_number):
    """
        Create a pdf file to store receipt
    """
    page = browser.page()
    receipt_reviewer = 0
    try:
        if page.locator("#receipt").is_visible(): 
            order_receipt_html = page.locator("#receipt").inner_html()
            pdf = PDF()
            pdf_file = "output/order_number-" + order_number + ".pdf"
            pdf.html_to_pdf(order_receipt_html, pdf_file)
            screenshot = screenshot_robot(order_number)
            embed_screenshot_to_receipt(screenshot, pdf_file)
        else: 
            receipt_reviewer = 1
    except Exception as e:
        receipt_reviewer = 1
        page.click("#order")
    return receipt_reviewer

def screenshot_robot(order_number):
    """
        Get the receipt robot order screenshot
    """
    page = browser.page()
    file_name = "output/robot_preview_screenshot_"+order_number+".png"
    page.screenshot(path=file_name)
    return file_name

def embed_screenshot_to_receipt(screenshot, pdf_file):
    """
        Add a screenshot to pdf
    """
    pdf = PDF()
    pdf.add_files_to_pdf([pdf_file, screenshot+":align=center"], pdf_file)

def archive_receipts():
    """
        Add all pdf's to a zip file
    """
    zip = Archive()
    zip.archive_folder_with_zip("./output", "./output/orders.zip", include="*.pdf")

