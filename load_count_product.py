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

        self.progress_label = tk.Label(root, text="Tiến trình:")
        self.progress_label.grid(row=1, column=0, padx=10, pady=10, sticky='w')

        self.progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
        self.progress.grid(row=1, column=1, columnspan=2, padx=10, pady=10)

        self.result_text = scrolledtext.ScrolledText(root, width=60, height=20)
        self.result_text.grid(row=2, column=0, columnspan=3, padx=10, pady=10)

        self.product_codes = []
        self.products = []

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if file_path:
            self.result_text.insert(tk.END, f"File selected: {file_path}\n")
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    self.product_codes = [line.strip() for line in file if line.strip()]
                self.result_text.insert(tk.END, f"Total product codes loaded: {len(self.product_codes)}\n")
            except (UnicodeDecodeError, IOError):
                messagebox.showerror("Error", "Không thể đọc file. Vui lòng kiểm tra mã hóa hoặc định dạng file.")
                return

    def load_data(self):
        if not self.product_codes:
            messagebox.showwarning("Warning", "Please open a file first.")
            return

        self.result_text.delete(1.0, tk.END)
        self.progress["value"] = 0

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

        def select_region_once(driver):
            try:
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//div[@data-company-name="Miền Nam"]'))
                ).click()
                time.sleep(2)
            except Exception:
                pass

        initial_url = "https://konni39.com"
        driver.get(initial_url)
        select_region_once(driver)

        total_products = len(self.product_codes)
        for i, code in enumerate(self.product_codes):
            code = code.strip()
            encoded_code = quote(code)
            url = f"https://konni39.com/shop?filter_2=9&search={encoded_code}"

            driver.get(url)
            driver.execute_script("window.stop();")
            time.sleep(1)

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            result_div = soup.find('div', class_='result-list')
            if result_div:
                result_span = result_div.find('span', string=lambda t: t and 'kết quả' in t)
                if result_span and '0' in result_span.get_text(strip=True):
                    self.products.append({"code": code, "quantity": 0, "brand": "N/A"})
                else:
                    product_link = soup.find('div', class_='list-products row justify-content-start').find('a', href=True)
                    if product_link:
                        product_url = "https://konni39.com" + product_link['href']
                        driver.get(product_url)
                        time.sleep(1)
                        product_soup = BeautifulSoup(driver.page_source, 'html.parser')

                        count_element = product_soup.find('input', {'id': 'free_qty'})
                        quantity = count_element['value'] if count_element else "Hết hàng"

                        label_element = product_soup.find('th', string=lambda text: text and 'Nhãn hiệu' in text)
                        brand = label_element.find_next_sibling('td').text.strip() if label_element else "Ko nhãn hiệu"

                        self.products.append({"code": code, "quantity": quantity, "brand": brand})
            else:
                self.products.append({"code": code, "quantity": "N/A", "brand": "N/A"})

            progress_percentage = (i + 1) / total_products * 100
            self.progress["value"] = progress_percentage
            self.root.update_idletasks()

        driver.quit()
        self.save_results()

    def save_results(self):
        txt_file = "product_results.txt"
        with open(txt_file, 'w', encoding='utf-8') as file:
            for product in self.products:
                file.write(f"{product['code']}: {product['quantity']}, {product['brand']}\n")
        self.result_text.insert(tk.END, f"Results saved to {txt_file}\n")

        df = pd.DataFrame(self.products)
        excel_file = "product_results.xlsx"
        df.to_excel(excel_file, index=False)
        self.result_text.insert(tk.END, f"Results saved to {excel_file}\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = ProductCheckerApp(root)
    root.mainloop()