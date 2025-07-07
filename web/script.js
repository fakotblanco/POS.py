console.log("✅ script.js cargado");

window.addEventListener("DOMContentLoaded", () => {
  console.log("✅ DOMContentLoaded");

  // Elementos principales
  const fileInput     = document.getElementById('fileInput');
  const scanInfo      = document.getElementById('scanInfo');
  const searchInput   = document.getElementById('search');
  const productSelect = document.getElementById('productSelect');
  const addManualBtn  = document.getElementById('addManual');
  const manualQty     = document.getElementById('manualQty');
  const manualTable   = document.querySelector('#manualTable tbody');
  const confirmManual = document.getElementById('confirmManual');
  const cancelManual  = document.getElementById('cancelManual');
  const historyTable  = document.querySelector('#historyTable tbody');

  console.log("✅ searchInput:", searchInput);

  // --- ESCANEO con foto ---
  fileInput.onchange = async () => {
    const file = fileInput.files[0];
    const data = new FormData();
    data.append('file', file);

    const resp1 = await fetch('/scan/', { method: 'POST', body: data });
    const js1   = await resp1.json();
    console.log('Respuesta /scan/:', js1);

    scanInfo.innerHTML = js1.code
      ? `<p>Código detectado: ${js1.code}</p>`
      : `<p style="color:red">Error: ${js1.error || 'No se detectó código'}</p>`;

    if (!js1.found) {
      scanInfo.innerHTML += `<p style="color:red">${js1.error || 'Producto no existe'}</p>`;
      return;
    }

    scanInfo.innerHTML += `
      <label>Cantidad a ingresar:
        <input type="number" id="qtyScan" value="1" min="1" style="width:4em">
      </label>
      <button id="updScan" class="btn-primary">Actualizar</button>
    `;

    document.getElementById('updScan').onclick = async () => {
      const qty = parseInt(document.getElementById('qtyScan').value, 10);
      const form = new FormData();
      form.append('product_id', js1.product.id);
      form.append('quantity',   qty);

      const resp2 = await fetch('/update_stock/', { method: 'POST', body: form });
      const js2   = await resp2.json();
      console.log('Respuesta /update_stock/:', js2);

      scanInfo.innerHTML += js2.success
        ? `<p style="color:green">Nuevo stock: ${js2.new_stock}</p>`
        : `<p style="color:red">${js2.error}</p>`;
      loadHistory();
    };
  };

  // --- ENTRADA MANUAL ---
  let timer;
  searchInput.addEventListener('input', (e) => {
    console.log('✅ oninput disparado:', e.target.value);
    clearTimeout(timer);
    timer = setTimeout(async () => {
      const q = encodeURIComponent(searchInput.value);
      console.log('→ GET /products/?q=', q);
      const res = await fetch(`/products/?q=${q}`);
      const list = await res.json();
      console.log('← respuesta products:', list);

      productSelect.innerHTML = '<option value="">- busca un producto -</option>';
      list.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.id;
        opt.text  = `${p.code} - ${p.name} (Stock: ${p.stock})`;
        productSelect.append(opt);
      });
    }, 300);
  });

  addManualBtn.onclick = () => {
    const id   = productSelect.value;
    const name = productSelect.selectedOptions[0]?.text || '';
    const qty  = parseInt(manualQty.value, 10) || 1;
    if (!id) {
      console.warn('Debe seleccionar un producto');
      return;
    }
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${id}</td>
      <td>${name}</td>
      <td>${qty}</td>
      <td><button class="btn-danger">X</button></td>
    `;
    tr.querySelector('button').onclick = () => tr.remove();
    manualTable.append(tr);
  };

  confirmManual.onclick = async () => {
    const rows = [...manualTable.children];
    for (let r of rows) {
      const [idCell, , qtyCell] = r.querySelectorAll('td');
      const form = new FormData();
      form.append('product_id', idCell.textContent);
      form.append('quantity',   qtyCell.textContent);
      const res = await fetch('/entry/', { method: 'POST', body: form });
      const js = await res.json();
      console.log('Respuesta /entry/:', js);
    }
    manualTable.innerHTML = '';
    alert('Entradas registradas');
    loadHistory();
  };

  cancelManual.onclick = () => {
    manualTable.innerHTML = '';
  };

  // --- HISTORIAL ---
  async function loadHistory() {
    historyTable.innerHTML = '';
    const res = await fetch('/entries/');
    const list = await res.json();
    console.log('Historial:', list);
    list.forEach(e => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${e.date}</td>
        <td>${e.code}</td>
        <td>${e.name}</td>
        <td>${e.quantity}</td>
      `;
      historyTable.append(tr);
    });
  }

  loadHistory();
});
