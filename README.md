
## Thiết lập CPLEX (license đầy đủ)

Gói `cplex` cài qua pip mặc định dùng bản Community Edition (giới hạn 1000 biến/ràng buộc).
Để dùng license Academic đầy đủ đã cài qua IBM CPLEX Studio, cần ghi đè file thư viện sau
mỗi lần tạo lại môi trường (`uv sync` hoặc clone sang máy mới):

```bash
cp ~/ibm/ILOG/CPLEX_Studio2211/cplex/bin/x86-64_linux/libcplex2220.so \
   .venv/lib/python3.10/site-packages/cplex/_internal/libcplex2220.so
cp ~/ibm/ILOG/CPLEX_Studio2211/cplex/bin/x86-64_linux/libcplex2220.so \
   .venv/bin/libcplex2220.so
```

Yêu cầu: đã cài IBM CPLEX Studio tại `~/ibm/ILOG/CPLEX_Studio2211` với license Academic hợp lệ.
