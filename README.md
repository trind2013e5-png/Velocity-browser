# PyBrowser

Trình duyệt viết bằng PyQt6. Phần render web dùng `QWebEngineView`
(Chromium nhúng sẵn trong Qt) để hiển thị trang đúng chuẩn — không có
cách nào trong PyQt6 hiển thị web hiện đại mà không có Chromium bên dưới,
trừ khi tự viết engine HTML/CSS/JS riêng. Toàn bộ phần giao diện, tab,
bookmark, lịch sử, ad-block, dark mode là code Python thuần, dễ đọc và
tùy biến thêm.

## Cài đặt & chạy

```bash
pip install -r requirements.txt
python main.py
```

## Cấu trúc thư mục

```
PyBrowser/
├── main.py                  # entry point
├── requirements.txt
└── core/
    ├── browser_window.py     # cửa sổ chính, ghép mọi thứ lại
    ├── tab_manager.py        # quản lý nhiều tab (QTabWidget)
    ├── toolbar.py             # thanh điều hướng + address bar
    ├── adblock.py             # chặn quảng cáo/theo dõi
    ├── dark_mode.py           # CSS/JS dark mode cho web + theme UI
    ├── bookmarks.py           # quản lý bookmark (JSON)
    ├── history.py             # quản lý lịch sử (JSON)
    ├── settings_manager.py    # quản lý settings.json
    ├── dialogs.py             # dialog Bookmark / History
    └── utils.py               # resolve_url (URL hay search query)
```

Dữ liệu người dùng (settings, bookmark, lịch sử, danh sách chặn quảng cáo)
được lưu ở `~/.pybrowser/`.

## Tính năng hiện có

- Đa tab, kéo thả sắp xếp, đóng/mở tab (`Ctrl+T`, `Ctrl+W`)
- Thanh địa chỉ thông minh: nhập domain hoặc từ khóa tìm kiếm đều được
- Bookmark: bấm sao trên toolbar hoặc `Ctrl+D`, xem/xóa trong menu Bookmark
- Lịch sử duyệt web, xem & xóa trong menu Lịch sử
- Chặn quảng cáo/theo dõi (menu Xem → Chặn quảng cáo)
- Dark mode cho cả trang web và khung giao diện (menu Xem → Dark mode)
- Phím tắt: `Ctrl+L` focus address bar, `Ctrl+T` tab mới, `Ctrl+W` đóng tab,
  `Ctrl+D` bookmark, `F5` reload

## Cách tùy biến thêm

- **Thêm domain chặn quảng cáo**: sửa `~/.pybrowser/adblock_list.txt`
  (mỗi dòng 1 domain), không cần sửa code.
- **Đổi search engine mặc định**: sửa `search_engine` trong
  `~/.pybrowser/settings.json`, ví dụ đổi sang Bing/DuckDuckGo.
- **Đổi trang chủ**: sửa `home_page` trong cùng file settings.json.
- **Đổi màu/giao diện**: sửa `APP_DARK_STYLESHEET` /
  `APP_LIGHT_STYLESHEET` trong `core/dark_mode.py` (cú pháp QSS, gần
  giống CSS).
- **Thêm tính năng mới** (ví dụ: extension hook, đồng bộ tab, reader
  mode...): thêm file mới trong `core/`, import và gọi từ
  `browser_window.py` — kiến trúc đang tách module rõ ràng nên không
  ảnh hưởng phần còn lại.

## Giới hạn cần biết

- Engine render là Chromium (qua Qt WebEngine) nên RAM/dung lượng cài
  đặt sẽ nặng hơn một trình duyệt viết engine riêng, nhưng đổi lại
  tương thích web tốt và ổn định.
- Ad-block hiện tại là danh sách domain tĩnh, không phải bộ lọc theo
  pattern phức tạp như uBlock Origin — đủ chặn phần lớn ad/tracker phổ
  biến, không phải toàn diện 100%.
