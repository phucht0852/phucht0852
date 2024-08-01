import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import pandas as pd
from datetime import datetime
import re

class ProductCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tải Dữ liệu - Danh mục")

        # Tạo các phần tử UI
        self.file_label = tk.Label(root, text="Chọn file URL sản phẩm:")
        self.file_label.grid(row=0, column=0, padx=10, pady=10, sticky='w')

        self.open_file_button = tk.Button(root, text="Open File", command=self.open_file)
        self.open_file_button.grid(row=0, column=1, padx=10, pady=10)

        self.load_button = tk.Button(root, text="Load", command=self.load_data)
        self.load_button.grid(row=0, column=2, padx=10, pady=10)

        self.clear_button = tk.Button(root, text="Clear", command=self.clear_data)
        self.clear_button.grid(row=0, column=3, padx=10, pady=10)

        self.progress_label = tk.Label(root, text="Tiến trình:")
        self.progress_label.grid(row=1, column=0, padx=10, pady=10, sticky='w')

        self.progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
        self.progress.grid(row=1, column=1, columnspan=3, padx=10, pady=10)

        self.result_text = scrolledtext.ScrolledText(root, width=80, height=20)
        self.result_text.grid(row=2, column=0, columnspan=4, padx=10, pady=10)

        self.product_urls = []
        self.products = []
        self.driver = None

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if file_path:
            self.result_text.insert(tk.END, f"File selected: {file_path}\n")
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    self.product_urls = [line.strip() for line in file if line.strip()]
                self.result_text.insert(tk.END, f"Total URLs loaded: {len(self.product_urls)}\n")
            except (UnicodeDecodeError, IOError):
                messagebox.showerror("Error", "Không thể đọc file. Vui lòng kiểm tra mã hóa hoặc định dạng file.")
                return

    def clear_data(self):
        self.result_text.delete(1.0, tk.END)
        self.progress["value"] = 0
        self.product_urls = []
        self.products = []

    def load_data(self):
        if not self.product_urls:
            messagebox.showwarning("Warning", "Please open a file first.")
            return

        self.result_text.delete(1.0, tk.END)
        self.progress["value"] = 0

        start_time = datetime.now()
        self.result_text.insert(tk.END, f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

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
        self.driver = webdriver.Chrome(options=chrome_options)

        def select_region_once(driver):
            try:
                region_element = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//div[@data-company-name="Miền Nam"]'))
                )
                region_element.click()
                self.result_text.insert(tk.END, "Chọn vùng: Miền Nam\n")
                time.sleep(2)
                return True
            except Exception:
                self.result_text.insert(tk.END, "Không cần chọn vùng\n")
                return False

        def extract_product_info(driver, url):
            driver.get(url)
            select_region_once(driver)
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Tìm số lượng sản phẩm
            result_list = soup.find('div', class_='result-list mb-4')
            if result_list:
                result_span = result_list.find('span', string=lambda text: 'kết quả' in text)
                if result_span:
                    # Sử dụng regex để trích xuất số từ chuỗi
                    match = re.search(r'\d+', result_span.text)
                    if match:
                        product_numbers = int(match.group())
                    else:
                        product_numbers = 0
                    self.result_text.insert(tk.END, f"URL: {url}, Số lượng sản phẩm: {product_numbers}\n")
                else:
                    product_numbers = 0
                    self.result_text.insert(tk.END, f"URL: {url}, Không tìm thấy số lượng sản phẩm\n")
            else:
                product_numbers = 0
                self.result_text.insert(tk.END, f"URL: {url}, Không tìm thấy số lượng sản phẩm\n")

            # Tìm danh sách URL sản phẩm
            url_list = []
            list_products = soup.find('div', class_='list-products row justify-content-start')
            if list_products:
                product_items = list_products.find_all('div', class_='product-item')
                for item in product_items:
                    product_link = item.find('a', href=True)
                    if product_link:
                        full_url = "https://konni39.com" + product_link['href']
                        url_list.append(full_url)

            # Tìm số trang
            max_page = 1
            pagination = soup.find('div', class_='list-product-pagination py-2 px-lg-3')
            if pagination:
                page_links = pagination.find_all('a', class_='link-hv')
                for link in page_links:
                    try:
                        page_num = int(link.text.strip())
                        if page_num > max_page:
                            max_page = page_num
                    except ValueError:
                        continue

            # Lặp qua các trang tiếp theo
            for page in range(2, max_page + 1):
                next_page_url = url + f"/page/{page}"
                driver.get(next_page_url)
                time.sleep(2)
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                list_products = soup.find('div', class_='list-products row justify-content-start')
                if list_products:
                    product_items = list_products.find_all('div', class_='product-item')
                    for item in product_items:
                        product_link = item.find('a', href=True)
                        if product_link:
                            full_url = "https://konni39.com" + product_link['href']
                            url_list.append(full_url)

            # Loại bỏ các URL trùng lặp
            url_list = list(set(url_list))

            return {
                "Product numbers": product_numbers,
                "URL list": url_list
            }

        total_products = len(self.product_urls)
        for i, url in enumerate(self.product_urls):
            try:
                product_info = extract_product_info(self.driver, url)
                self.products.append(product_info)
                self.result_text.insert(tk.END, f"Product {i+1}/{total_products} loaded: {url}\n")
            except Exception as e:
                self.result_text.insert(tk.END, f"Error loading product {i+1}/{total_products}: {e}\n")

            progress_percentage = (i + 1) / total_products * 100
            self.progress["value"] = progress_percentage
            self.root.update_idletasks()

        self.driver.quit()

        end_time = datetime.now()
        self.result_text.insert(tk.END, f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

        self.result_text.insert(tk.END, "\nData loaded successfully.\n")
        self.save_to_files(start_time, end_time)

    def save_to_files(self, start_time, end_time):
        # Tạo DataFrame với các cột được xác định
        df = pd.DataFrame(self.products, columns=["Product numbers", "URL list"])
        # Thêm hàng đầu tiên với thông tin thời gian
        df.loc[-1] = [f'Thời gian bắt đầu: {start_time.strftime("%Y-%m-%d %H:%M:%S")}', f'Thời gian hoàn tất: {end_time.strftime("%Y-%m-%d %H:%M:%S")}']
        df.index = df.index + 1  # Dịch chỉ số index lên 1
        df = df.sort_index()  # Sắp xếp lại index
        df.to_excel("product_data.xlsx", index=False)
        self.result_text.insert(tk.END, "Data saved to product_data.xlsx\n")

        # Lưu vào file văn bản
        with open("product_urls.txt", "w", encoding="utf-8") as file:
            all_urls = set()  # Sử dụng set để loại bỏ các URL trùng lặp
            for product in self.products:
                all_urls.update(product["URL list"])
            for url in all_urls:
                file.write(url + "\n")
        self.result_text.insert(tk.END, "Data saved to product_urls.txt\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = ProductCheckerApp(root)
    root.mainloop()