# Bài A2 – Thu thập và xử lý dữ liệu thời tiết

Chương trình sử dụng **Open-Meteo Forecast API** để thu thập dữ liệu dự báo thời tiết theo giờ tại Hà Nội. Dữ liệu được làm sạch, lưu vào JSON, đọc lại và xử lý bằng các chức năng tìm kiếm, lọc, sắp xếp và thống kê.

## 1. Công nghệ sử dụng

- **Ngôn ngữ:** Python 3.10 trở lên.
- **API:** [Open-Meteo Forecast API](https://open-meteo.com/en/docs).
- **Thư viện bên ngoài:** `requests`.
- **Lưu trữ:** JSON.
- **Giao diện:** Terminal / Command Prompt.

Các thư viện `json`, `math`, `datetime`, `pathlib` và `typing` thuộc Python Standard Library, không cần cài đặt riêng.

## 2. Phạm vi thu thập dữ liệu

Địa điểm được cố định trong mã nguồn tại Hà Nội:

| Thuộc tính | Giá trị |
|---|---:|
| Thành phố | Hà Nội |
| Latitude | `21.0285` |
| Longitude | `105.8542` |
| Múi giờ | `Asia/Ho_Chi_Minh` |
| Khoảng dự báo | 1 ngày |
| Tần suất dữ liệu | Theo giờ |

Mỗi bản ghi gồm 7 thuộc tính:

| Thuộc tính | Mô tả | Đơn vị / kiểu dữ liệu |
|---|---|---|
| `time` | Thời điểm dự báo | ISO 8601 |
| `city` | Địa điểm | Chuỗi |
| `temperature` | Nhiệt độ tại độ cao 2 m | °C |
| `humidity` | Độ ẩm tương đối | % |
| `precipitation` | Lượng mưa | mm |
| `wind_speed` | Tốc độ gió tại độ cao 10 m | km/h |
| `weather_code` | Mã trạng thái thời tiết theo WMO | Số nguyên |

Nguồn API: <https://api.open-meteo.com/v1/forecast>

## 3. Cấu trúc thư mục

```text
gk-crawl-data/
├── main.py                # Chương trình chính
├── requirements.txt       # Danh sách thư viện cần cài
├── README.md              # Tài liệu hướng dẫn
├── .gitignore             # Các tệp/thư mục Git bỏ qua
```

`weather_data.json` được tạo cùng thư mục với `main.py`. Tệp này có thể được đưa vào `.gitignore` vì là dữ liệu đầu ra sinh tự động.

## 4. Cài đặt

Yêu cầu đã cài Python và có thể gọi Python từ Terminal. Các lệnh dưới đây dùng PowerShell trên Windows.

### Bước 1: Mở thư mục dự án

```powershell
cd "gk-crawl-data"
```

### Bước 2: Tạo môi trường ảo

```powershell
python -m venv .venv
```

Nếu máy có nhiều bản Python hoặc lệnh `python` chưa trỏ đến phiên bản mong muốn, dùng đường dẫn đầy đủ đến Python để tạo môi trường ảo.

### Bước 3: Kích hoạt môi trường ảo

```powershell
.\.venv\Scripts\Activate.ps1
```

Sau khi kích hoạt, tên môi trường `(.venv)` sẽ xuất hiện ở đầu dòng lệnh.

Nếu PowerShell chặn việc chạy script kích hoạt, có thể không cần activate mà gọi trực tiếp Python trong môi trường ảo ở các bước tiếp theo.

### Bước 4: Cài thư viện

```powershell
python -m pip install -r requirements.txt
```

Hoặc không activate môi trường ảo:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 5. Chạy chương trình

Khi đã kích hoạt `.venv`:

```powershell
python main.py
```

Hoặc gọi trực tiếp interpreter trong môi trường ảo:

```powershell
.\.venv\Scripts\python.exe main.py
```

Khi khởi động, chương trình thực hiện theo thứ tự:

1. Gửi HTTP GET request đến Open-Meteo API.
2. Kiểm tra phản hồi và trích xuất dữ liệu trong trường `hourly`.
3. Làm sạch, chuẩn hóa và loại bỏ bản ghi trùng thời gian.
4. Lưu dữ liệu vào `weather_data.json`.
5. Đọc lại dữ liệu từ JSON.
6. Hiển thị thống kê ban đầu và menu thao tác.

Nếu API không truy cập được hoặc trả về dữ liệu không hợp lệ, chương trình sẽ thử sử dụng `weather_data.json` đã lưu từ lần chạy trước. Nếu không có tệp dữ liệu cũ, chương trình sẽ thông báo lỗi và kết thúc.

## 6. Các chức năng

Sau khi dữ liệu được tải và đọc thành công, chương trình hiển thị menu:

| Lựa chọn | Chức năng | Mô tả |
|---|---|---|
| `1` | Hiển thị dữ liệu | In các bản ghi thời tiết dưới dạng bảng trong Terminal. |
| `2` | Tìm kiếm theo thời gian | Nhập ngày; có thể nhập thêm giờ và phút để thu hẹp kết quả. |
| `3` | Lọc theo nhiệt độ | Nhập ngưỡng nhiệt độ; lấy các bản ghi có nhiệt độ lớn hơn hoặc bằng ngưỡng. |
| `4` | Sắp xếp dữ liệu | Sắp xếp theo thời gian, nhiệt độ, độ ẩm, lượng mưa hoặc tốc độ gió; tăng dần hoặc giảm dần. |
| `5` | Thống kê dữ liệu | Tính các chỉ số tổng hợp về nhiệt độ, độ ẩm và lượng mưa. |
| `0` | Thoát | Kết thúc chương trình. |

### Tìm kiếm theo thời gian

Nhập ngày theo định dạng `dd/mm/yyyy`. Có thể nhấn Enter ở trường giờ để bỏ qua giờ và lấy toàn bộ bản ghi trong ngày. Nếu đã nhập giờ, có thể nhấn Enter ở trường phút để bỏ qua phút.

Ví dụ:

```text
Nhap ngay (dd/mm/yyyy): 12/11/2026
Nhap gio (0-23, Enter de bo qua): 08
Nhap phut (0-59, Enter de bo qua): 00
```

**Lưu ý:** Dữ liệu được lấy theo giờ nên thời điểm dự báo thường có phút là `00`. Nhập phút khác `00` thường sẽ không có kết quả.

### Thống kê

Chương trình thực hiện các thống kê sau:

- Nhiệt độ trung bình, cao nhất và thấp nhất.
- Độ ẩm trung bình.
- Tổng lượng mưa dự báo.
- Số giờ có lượng mưa lớn hơn `0 mm`.

Các phép tính bỏ qua giá trị không hợp lệ hoặc bị thiếu.

## 7. Làm sạch dữ liệu và xử lý lỗi

Chương trình thực hiện một số kiểm tra trước khi lưu dữ liệu:

- Kiểm tra trường thời gian và các mảng dữ liệu dự báo có đúng kiểu hay không.
- Chuyển các giá trị đo sang kiểu số; giá trị không chuyển đổi được hoặc không hữu hạn được gán `None`.
- Kiểm tra miền giá trị của độ ẩm, lượng mưa, tốc độ gió và mã thời tiết.
- Bỏ qua thời gian không hợp lệ và loại bỏ bản ghi trùng thời gian.
- Bỏ bản ghi nếu tất cả các chỉ số thời tiết đều thiếu hoặc không hợp lệ.
- Xử lý lỗi kết nối, HTTP, JSON sai định dạng và lỗi đọc tệp JSON.
- Khi API gặp lỗi, sử dụng dữ liệu JSON cũ nếu tệp này tồn tại và hợp lệ.

## 8. Đối chiếu yêu cầu bài A2

| STT | Yêu cầu | Phần triển khai |
|---:|---|---|
| 1 | Thu thập từ ít nhất một nguồn trực tuyến | Open-Meteo Forecast API |
| 2 | Trích xuất tối thiểu 5 thuộc tính | 7 thuộc tính: `time`, `city`, `temperature`, `humidity`, `precipitation`, `wind_speed`, `weather_code` |
| 3 | Làm sạch dữ liệu | Kiểm tra kiểu, giá trị, thời gian và bản ghi trùng |
| 4 | Chuyển về cấu trúc Python phù hợp | Danh sách các dictionary (`list[dict]`) |
| 5 | Lưu CSV hoặc JSON | `weather_data.json` |
| 6 | Đọc lại dữ liệu đã lưu | Đọc bằng `json.load()` |
| 7 | Tìm kiếm / lọc dữ liệu | Tìm theo thời gian, lọc theo nhiệt độ |
| 8 | Sắp xếp theo tiêu chí | Sắp xếp theo thời gian hoặc các chỉ số thời tiết |
| 9 | Thực hiện ít nhất 3 thống kê | Thống kê nhiệt độ, độ ẩm và lượng mưa |
| 10 | Xử lý dữ liệu rỗng hoặc sai định dạng | Kiểm tra phản hồi API, JSON, trường dữ liệu và lỗi kết nối |

## 9. Tham khảo

- Open-Meteo – Weather Forecast API: <https://open-meteo.com/en/docs>
- Python – `venv`: <https://docs.python.org/3/library/venv.html>
- Python – `json`: <https://docs.python.org/3/library/json.html>
