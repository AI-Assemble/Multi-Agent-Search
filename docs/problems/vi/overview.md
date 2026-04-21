# Bài Toán Tìm Kiếm Đa Tác Tử

**Hạn nộp:** 06/05/2026 (dd-mm-yyyy)

## Mục Lục

* [Q1 - Reflex Agent](q1.md)
* [Q2 - Minimax](q2.md)
* [Q3 - Alpha-Beta Pruning](q3.md)
* [Q4 - Expectimax](q4.md)
* [Q5 - Evaluation Function](q5.md)
* [Q6 - AI Usage Reflection và Collaborators](q6.md)

---

## Giới Thiệu

Trong project này, bạn sẽ thiết kế các agent cho phiên bản Pacman kinh điển, bao gồm cả ghost. Trong quá trình đó, bạn sẽ cài đặt cả minimax và expectimax search, đồng thời thử thiết kế hàm đánh giá.

Code base của project này không thay đổi nhiều so với project trước, nhưng hãy bắt đầu bằng một bản cài đặt mới thay vì trộn lẫn file từ project 1.

Giống project 1, project này có autograder để bạn chấm bài trên máy của mình. Có thể chạy cho tất cả câu hỏi bằng lệnh:
```bash
python autograder.py
```
Có thể chạy cho một câu cụ thể, ví dụ q2, bằng:
```bash
python autograder.py -q q2
```
Có thể chạy cho một test cụ thể bằng các lệnh dạng:
```bash
python autograder.py -t test_cases/q2/0-small-tree
```
Mặc định, autograder hiển thị đồ họa khi dùng tùy chọn `-t`, nhưng không hiển thị khi dùng `-q`. Bạn có thể buộc bật đồ họa bằng cờ `--graphics`, hoặc buộc tắt bằng `--no-graphics`.

Xem tutorial autograder ở Project 0 để biết thêm chi tiết cách sử dụng.

## Ba Cách Làm Việc

Repository này hiện hỗ trợ 3 cách chạy song song:

1. `Chế độ tương thích kiểu cũ`: dùng các file ở thư mục gốc như `pacman.py`, `autograder.py`, `multiAgents.py`.
2. `Chế độ cấu trúc mới`: làm việc trực tiếp với code dưới `src/core` và `tests`.
3. `Chế độ Taskfile`: dùng các target trong `Taskfile.yml` để chạy launcher và test một cách nhất quán giữa các môi trường (CI dùng cùng targets này).

### Cách 1: Tương thích kiểu cũ

Đây là cách phù hợp nhất nếu bạn muốn làm đúng theo câu lệnh trong docs gốc.

Chạy game từ thư mục gốc:
```bash
python pacman.py
python pacman.py -p ReflexAgent -l testClassic
```

Chạy autograder từ thư mục gốc:
```bash
python autograder.py
python autograder.py -q q2 --no-graphics
```

Nếu làm bài theo đúng wording cũ của project, file bạn thường sửa là:
```bash
multiAgents.py
```

### Cách 2: Cấu trúc mới

Đây là cách phù hợp hơn nếu bạn muốn bám theo structure hiện tại của repo.

Chạy Pacman trực tiếp từ package mới:
```bash
PYTHONPATH=src/core python -m controller.pacman -p ReflexAgent -l testClassic
```

Chạy autograder theo structure mới:
```bash
PYTHONPATH="tests;src/core" python -m autograder -q q2 --no-graphics
```

Nếu làm việc trực tiếp với code chuẩn của cấu trúc mới, file bạn thường sửa là:
```bash
src/core/agents/multiAgents.py
```

Code của project này bao gồm các file sau (được cung cấp dưới dạng zip archive).

**Các file bạn sẽ chỉnh sửa:**
* `multiAgents.py`: Nơi chứa toàn bộ multi-agent search agent của bạn.

**Các file bạn có thể muốn xem:**
* `pacman.py`: File chính chạy game Pacman. File này cũng mô tả kiểu `GameState` của Pacman, sẽ được dùng rất nhiều trong project.
* `game.py`: Logic vận hành thế giới Pacman. File này mô tả các kiểu hỗ trợ như `AgentState`, `Agent`, `Direction`, và `Grid`.
* `util.py`: Các cấu trúc dữ liệu hữu ích để cài đặt search algorithm. Bạn không bắt buộc dùng trong project này, nhưng có thể thấy một số hàm khác ở đây hữu ích.

**Các file hỗ trợ có thể bỏ qua:**
* `graphicsDisplay.py`: Đồ họa cho Pacman
* `graphicsUtils.py`: Hỗ trợ đồ họa cho Pacman
* `textDisplay.py`: Đồ họa dạng ASCII
* `ghostAgents.py`: Agent điều khiển ghost
* `keyboardAgents.py`: Giao diện bàn phím điều khiển Pacman
* `layout.py`: Đọc file layout và lưu nội dung layout
* `autograder.py`: Trình autograder của project
* `testParser.py`: Parser cho test và file lời giải của autograder
* `testClasses.py`: Các lớp test chung cho autograding
* `test_cases/`: Thư mục chứa test case cho từng câu hỏi
* `multiagentTestClasses.py`: Các lớp test riêng cho project 3

**Files to Edit and Submit:** Bạn sẽ điền các phần còn thiếu trong `multiAgents.py` trong quá trình làm bài. Khi hoàn thành, hãy nộp các file này lên Gradescope (ví dụ, có thể upload toàn bộ file `.py` trong thư mục). Vui lòng không thay đổi các file khác trong bộ mã được cung cấp.

**Đánh giá:** Mã của bạn sẽ được autograde dựa trên tính đúng kỹ thuật. Vui lòng không đổi tên các hàm hoặc class đã được cung cấp, nếu không bạn có thể làm autograder lỗi. Tuy nhiên, tính đúng của phần cài đặt mới là tiêu chí cuối cùng quyết định điểm. Nếu cần, chúng tôi sẽ rà soát và chấm thủ công để đảm bảo bạn nhận đủ điểm xứng đáng.

**Liêm chính học thuật:** Chúng tôi sẽ kiểm tra mã của bạn với các bài nộp khác để phát hiện sự trùng lặp logic. Nếu bạn sao chép mã của người khác rồi sửa nhẹ và nộp, chúng tôi sẽ phát hiện được. Các bộ phát hiện gian lận này rất khó qua mặt, nên vui lòng không thử. Chúng tôi tin các bạn chỉ nộp bài do chính mình làm; đừng làm chúng tôi thất vọng. Nếu vi phạm, chúng tôi sẽ áp dụng các hình thức xử lý nghiêm khắc nhất có thể.

**Tìm hỗ trợ:** Bạn không hề đơn độc. Nếu bị kẹt ở đâu đó, hãy liên hệ đội ngũ giảng dạy để được giúp đỡ. Office hours, section và diễn đàn thảo luận đều dành để hỗ trợ bạn; hãy sử dụng chúng. Nếu bạn không tham gia được office hours, hãy báo cho chúng tôi để sắp xếp thêm lịch. Chúng tôi muốn các project mang tính học tập và tạo động lực, không gây nản lòng. Nhưng chúng tôi không thể biết lúc nào và cách nào để hỗ trợ nếu bạn không lên tiếng.

**Thảo luận:** Vui lòng cẩn thận, không đăng spoiler.

---

## Bắt Đầu Với Multi-Agent Pacman

Đầu tiên, chạy một ván Pacman cổ điển bằng lệnh:
```bash
python pacman.py
```
và dùng các phím mũi tên để di chuyển. Tiếp theo, chạy `ReflexAgent` được cung cấp trong `multiAgents.py`:
```bash
python pacman.py -p ReflexAgent
```
Lưu ý rằng agent này chơi khá tệ ngay cả ở layout đơn giản:
```bash
python pacman.py -p ReflexAgent -l testClassic
```
Hãy xem code của nó (trong `multiAgents.py`) và chắc chắn bạn hiểu nó đang làm gì.

Hoặc chạy launcher qua Taskfile (ghi đè agent/layout bằng biến môi trường):

```bash
task run:pacman
PACMAN_AGENT=ReflexAgent PACMAN_LAYOUT=testClassic task run:pacman
```

---

## Nộp Bài

Để nộp project, hãy upload các file Python bạn đã chỉnh sửa. Ví dụ, dùng chức năng upload của Gradescope cho toàn bộ file `.py` trong thư mục project. Nhớ tag bạn cùng nhóm trên Gradescope như một phần của bài nộp.
