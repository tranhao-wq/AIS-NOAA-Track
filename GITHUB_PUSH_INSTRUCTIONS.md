# Hướng dẫn đẩy mã nguồn lên GitHub

Để đẩy mã nguồn lên repository GitHub https://github.com/tranhao-wq/AIS-NOAA-Track, hãy làm theo các bước sau:

## 1. Khởi tạo Git repository (nếu chưa có)

```bash
git init
```

## 2. Thêm remote repository

```bash
git remote add origin https://github.com/tranhao-wq/AIS-NOAA-Track.git
```

## 3. Thêm tất cả các file vào staging area

```bash
git add .
```

## 4. Commit các thay đổi

```bash
git commit -m "Initial commit: AIS Marine Traffic Analyzer"
```

## 5. Đẩy mã nguồn lên GitHub

```bash
git push -u origin main
```

Nếu branch mặc định là `master` thay vì `main`, hãy sử dụng:

```bash
git push -u origin master
```

## Lưu ý

- Nếu bạn chưa đăng nhập vào GitHub, bạn sẽ được yêu cầu nhập thông tin đăng nhập
- Nếu bạn sử dụng xác thực hai yếu tố, bạn cần tạo một Personal Access Token trên GitHub và sử dụng nó thay cho mật khẩu
- Nếu bạn gặp lỗi khi push, hãy thử pull trước:

```bash
git pull origin main --rebase
```

Sau đó push lại:

```bash
git push -u origin main
```