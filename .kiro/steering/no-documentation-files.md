---
inclusion: always
---

# Quy tắc: Không tạo file tài liệu không cần thiết

## Nguyên tắc chính

**KHÔNG BAO GIỜ** tạo các file sau đây trừ khi người dùng **YÊU CẦU RÕ RÀNG**:

- ❌ README.md
- ❌ CHANGELOG.md
- ❌ TODO.md
- ❌ NOTES.md
- ❌ SUMMARY.md
- ❌ GUIDE.md
- ❌ INSTRUCTIONS.md
- ❌ Bất kỳ file markdown tài liệu nào khác

## Lý do

1. **Lãng phí thời gian**: Người dùng muốn code hoạt động, không phải đọc tài liệu
2. **Gây nhiễu**: Tạo ra các file không cần thiết trong dự án
3. **Không có giá trị**: Thông tin đã có trong code và commit messages

## Khi nào được tạo file tài liệu?

Chỉ khi người dùng **YÊU CẦU RÕ RÀNG**:
- "Tạo file README"
- "Viết tài liệu hướng dẫn"
- "Làm file CHANGELOG"

## Thay vào đó hãy làm gì?

✅ Tập trung vào:
- Viết code chất lượng với comments rõ ràng
- Sửa lỗi và cải thiện tính năng
- Tối ưu hiệu suất
- Đảm bảo code hoạt động đúng

✅ Khi hoàn thành công việc:
- Tóm tắt ngắn gọn những gì đã làm (2-3 câu)
- KHÔNG tạo file markdown để tóm tắt
- KHÔNG liệt kê chi tiết từng thay đổi

## Ví dụ

### ❌ SAI - Không làm điều này:
```
Tôi đã hoàn thành. Để tóm tắt, tôi sẽ tạo file SUMMARY.md...
```

### ✅ ĐÚNG - Làm như này:
```
Đã hoàn thành: Xóa toàn bộ Flet, cải thiện giao diện PyQt6 với theme hiện đại, 
gradient buttons, spacing tốt hơn và thêm emoji icons.
```

## Ghi nhớ

> "Code is the documentation. If you need to write docs, your code isn't clear enough."

**Luôn ưu tiên code > documentation files**
