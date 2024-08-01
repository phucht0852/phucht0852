import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import scrolledtext
from tkinter import ttk
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from urllib.parse import quote

class ProductCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Product Checker")

        # Tạo các phần tử UI
        self.file_label = tk.Label(root, text="Chọn file mã sản phẩm:")
        self.file_label.grid(row=0, column=0, padx=10, pady=10, sticky='w')

        self.open_file_button = tk.Button(root, text="Open File", command=self.open_file)
        self.open_file_button.grid(row=0, column=1, padx=10, pady=10)

        self.load_button = tk.Button(root, text="Load", command=self.load_data)
        self.load_button.grid(row=0, column=2, padx=10, pady=10)

        # Thanh tiến độ
        self.progress_label = tk.Label(root, text="Tiến trình:")
        self.progress_label.grid(row=1, column=0, padx=10, pady=10, sticky='w')

        self.progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
        self.progress.grid(row=1, column=1, columnspan=2, padx=10, pady=10)

        self.result_text = scrolledtext.ScrolledText(root, width=60, height=20)
        self.result_text.grid(row=2, column=0, columnspan=3, padx=10, pady=10)

        self.search_label = tk.Label(root, text="Tìm kiếm mã sản phẩm:")
        self.search_label.grid(row=3, column=0, padx=10, pady=10, sticky='w')

        self.search_entry = tk.Entry(root, width=30)
        self.search_entry.grid(row=3, column=1, padx=10, pady=10, sticky='w')

        self.find_button = tk.Button(root, text="Find", command=self.find_product)
        self.find_button.grid(row=3, column=2, padx=10, pady=10)

        # Thêm nút Count
        self.count_button = tk.Button(root, text="Count", command=self.count_available_products, state=tk.DISABLED)
        self.count_button.grid(row=4, column=0, columnspan=3, padx=10, pady=10)

        self.product_availability = {}
        self.file_path = None
        self.product_codes = []

    def open_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if self.file_path:
            self.result_text.insert(tk.END, f"File selected: {self.file_path}\n")
            try:
                with open(self.file_path, 'r', encoding='utf-8') as file:
                    # Chỉ đọc 50 dòng đầu tiên
                    self.product_codes = [line.strip() for line in file if line.strip()][:100]  
            except (UnicodeDecodeError, IOError):
                messagebox.showerror("Error", "Không thể đọc file. Vui lòng kiểm tra mã hóa hoặc định dạng file.")
                return

    def load_data(self):
        if not self.file_path:
            messagebox.showwarning("Warning", "Please open a file first.")
            return

        # Xóa nội dung cũ và thiết lập thanh tiến độ
        self.result_text.delete(1.0, tk.END)
        self.progress["value"] = 0

        # Bắt đầu đo thời gian
        start_time = time.time()

        # Thiết lập Selenium WebDriver
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--media-cache-size=1")
        chrome_options.add_experimental_option("prefs", {
            "profile.managed_default_content_settings.images": 2
        })
        driver = webdriver.Chrome(options=chrome_options)

        def block_unwanted_resources(driver):
            driver.execute_cdp_cmd('Network.setBlockedURLs', {
                'urls': ['https://sp.zalo.me/plugins/sdk.js']
            })
        block_unwanted_resources(driver)

        def select_region_once(driver):
            try:
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//div[@data-company-name="Miền Nam"]'))
                ).click()
                time.sleep(2)
            except Exception:
                pass

        # Chọn miền một lần khi vào trang
        initial_url = "https://konni39.com"
        driver.get(initial_url)
        select_region_once(driver)

        total_products = len(self.product_codes)
        available_products = []
        unavailable_products = []

        for i, code in enumerate(self.product_codes):
            code = code.strip()
            if code.isdigit() or not ' ' in code or code.isalnum():
                url = f"https://konni39.com/shop?filter_2=9&search={code}"
            else:
                encoded_code = quote(code)
                url = f"https://konni39.com/shop?filter_2=9&search={encoded_code}"

            driver.get(url)
            driver.execute_script("window.stop();")
            time.sleep(1)

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            result_div = soup.find('div', class_='result-list')
            if result_div:
                result_span = result_div.find('span', string=lambda t: t and 'kết quả' in t)
                if result_span:
                    result_text = result_span.get_text(strip=True)
                    if '0' in result_text:
                        unavailable_products.append(f"{code} 0")
                    else:
                        available_products.append(f"{code} 1")
                else:
                    available_products.append(f"{code}: 1")
            else:
                available_products.append(f"{code}: 1")

            progress_percentage = (i + 1) / total_products * 100
            self.progress["value"] = progress_percentage
            self.root.update_idletasks()

        driver.quit()

        end_time = time.time()
        elapsed_time = end_time - start_time

        # Hiển thị kết quả vào ô TextBox
        self.result_text.insert(tk.END, f"Thời gian thực thi: {elapsed_time:.2f} giây\n")
        self.result_text.insert(tk.END, "Sản phẩm có sẵn:\n")
        for product in available_products:
            self.result_text.insert(tk.END, f"{product}\n")

        self.result_text.insert(tk.END, "\nSản phẩm không có sẵn:\n")
        for product in unavailable_products:
            self.result_text.insert(tk.END, f"{product}\n")

        self.result_text.insert(tk.END, f"\nTotal valid product codes: {len(self.product_codes)}\n")
        self.result_text.insert(tk.END, "\nData loaded successfully.\n")

        # Cập nhật dữ liệu
        self.product_availability.update({code.split(':')[0]: 1 for code in available_products})
        self.product_availability.update({code.split(':')[0]: 0 for code in unavailable_products})

        # Cập nhật trạng thái của nút Count
        self.count_button.config(state=tk.NORMAL)

    def find_product(self):
        search_code = self.search_entry.get().strip()
        if search_code in self.product_availability:
            availability = self.product_availability[search_code]
            result = "Available" if availability == 1 else "Not Available"
            self.result_text.insert(tk.END, f"Product {search_code}: {result}\n")
        else:
            self.result_text.insert(tk.END, f"Product {search_code} not found in the results.\n")

    def count_available_products(self):
        available_products = [code for code, available in self.product_availability.items() if available == 1]
        self.result_text.insert(tk.END, "\nMã sản phẩm có sẵn:\n")
        for code in available_products:
            self.result_text.insert(tk.END, f"{code}\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = ProductCheckerApp(root)
    root.mainloop()
