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

class ProductCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tải dữ liệu sản phẩm")

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

        self.login_button = tk.Button(root, text="Login", command=self.manual_login)
        self.login_button.grid(row=3, column=0, padx=10, pady=10)

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

    def manual_login(self):
        chrome_options = Options()
        self.driver = webdriver.Chrome(options=chrome_options)
        login_url = "https://konni39.com/web/login"
        self.driver.get(login_url)
        messagebox.showinfo("Login", "Please log in manually and then click OK.")
        self.result_text.insert(tk.END, "Đăng nhập thành công\n")
        self.driver.quit()

        # Reinitialize driver with headless options
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

    def load_data(self):
        if not self.product_urls:
            messagebox.showwarning("Warning", "Please open a file first.")
            return

        if not self.driver:
            messagebox.showwarning("Warning", "Please log in first.")
            return

        self.result_text.delete(1.0, tk.END)
        self.progress["value"] = 0

        start_time = datetime.now()
        self.result_text.insert(tk.END, f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

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

        def extract_text_from_element(element):
            if element:
                for row in element.find_all('tr'):
                    cells = row.find_all(['th', 'td'])
                    if len(cells) == 2:
                        field_name = cells[0].get_text(strip=True)
                        field_value = cells[1].get_text(strip=True)
                        self.result_text.insert(tk.END, f"{field_name}: {field_value}\n")

        def get_product_info(driver, url):
            driver.get(url)
            region_selected = select_region_once(driver)
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            product_name = soup.find('div', id='product_detail_name')
            if product_name:
                product_name = product_name.find('p').text.strip()
            else:
                product_name = "N/A"
            self.result_text.insert(tk.END, f"Tên sản phẩm: {product_name}\n")
            barcode = soup.find('span', class_='span-barcode text-blog-6')
            if barcode:
                barcode = barcode.text.strip()
            else:
                barcode = "N/A"
            self.result_text.insert(tk.END, f"Mã sản phẩm: {barcode}\n")
            price = soup.find('div', class_='div_price_left')
            if price:
                price = price.find('span', class_='price_x_retail_price').text.strip()
            else:
                # Tìm giá tiền trong div thay thế
                price = soup.find('div', class_='detail-attributes')
                if price:
                    price = price.find('p', class_='price_mobile').text.strip()
                else:
                    price = "N/A"
            self.result_text.insert(tk.END, f"Giá: {price}\n")
            variants = [label.text.strip() for label in soup.select('li.variant_attribute label')]
            if not variants:
                variants = ["1 loại"]
            self.result_text.insert(tk.END, f"Loại: {variants}\n")

            count_element = soup.find('input', {'id': 'free_qty'})
            if count_element:
                count = count_element['value']
                self.result_text.insert(tk.END, f"Số lượng sản phẩm: {count}\n")
            else:
                count = "Hết hàng"
                self.result_text.insert(tk.END, "Không tìm thấy trường số lượng, sản phẩm hết hàng.\n")

            # Tìm và in ra thông tin sản phẩm
            product_info_element = soup.find('div', class_='bg-head-body-content mx-n3 p-3 position-relative mb-3')
            if product_info_element:
                self.result_text.insert(tk.END, "Thông tin sản phẩm:\n")
                extract_text_from_element(product_info_element)

            # Tìm nhãn hiệu trong phần thông tin sản phẩm
            label = "Ko nhãn hiệu"
            label_element = product_info_element.find('th', string=lambda text: text and 'Nhãn hiệu' in text)
            if label_element:
                label = label_element.find_next_sibling('td').text.strip()
                self.result_text.insert(tk.END, f"Nhãn hiệu: {label}\n")
            else:
                self.result_text.insert(tk.END, "Không tìm thấy nhãn hiệu\n")

            return {
                "product_name": product_name,
                "barcode": barcode,
                "price": price,
                "variants": variants,
                "count": count,
                "label": label,
                "region_selected": region_selected
            }

        total_products = len(self.product_urls)
        for i, url in enumerate(self.product_urls):
            try:
                if not url.startswith("http"):
                    raise ValueError("Invalid URL")
                product_info = get_product_info(self.driver, url)
                self.products.append(product_info)
                self.result_text.insert(tk.END, f"Product {i+1}/{total_products} loaded: {product_info['product_name']}\n")
                self.result_text.insert(tk.END, f"\n")
            except Exception as e:
                self.result_text.insert(tk.END, f"Error loading product {i+1}/{total_products}: {e}\n")

            progress_percentage = (i + 1) / total_products * 100
            self.progress["value"] = progress_percentage
            self.root.update_idletasks()

        self.driver.quit()

        end_time = datetime.now()
        self.result_text.insert(tk.END, f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

        self.result_text.insert(tk.END, "\nData loaded successfully.\n")
        self.save_to_excel(start_time, end_time)

    def save_to_excel(self, start_time, end_time):
        df = pd.DataFrame(self.products)
        # Thêm hàng đầu tiên với thông tin thời gian
        df.loc[-1] = [start_time.strftime('%Y-%m-%d %H:%M:%S'), end_time.strftime('%Y-%m-%d %H:%M:%S'), start_time.strftime('%Y-%m-%d'), start_time.strftime('%H:%M:%S')] + [''] * (len(df.columns) - 4)
        df.index = df.index + 1  # Dịch chỉ số index lên 1
        df = df.sort_index()  # Sắp xếp lại index
        df.to_excel("product_data_list.xlsx", index=False)
        self.result_text.insert(tk.END, "Data saved to product_data_list.xlsx\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = ProductCheckerApp(root)
    root.mainloop()