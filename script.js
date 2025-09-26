function registerAttendance() {
  const container = document.querySelector(".container");
  let msg = document.createElement("p");
  msg.textContent = "✅ تم تسجيل الحضور بنجاح!";
  msg.style.color = "green";
  msg.style.marginTop = "15px";
  container.appendChild(msg);
  setTimeout(() => msg.remove(), 5000);
}

async function analyzeWithAI() {
  const resultDiv = document.getElementById("ai-result");
  resultDiv.innerHTML = "⏳ جاري التحليل...";

  try {
    let response = await fetch("http://127.0.0.1:5000/analyze");
    let data = await response.json();

    resultDiv.innerHTML = "<h3>🔍 المحتوى المرتب:</h3>";
    let ul = document.createElement("ul");
    data.forEach(item => {
      let li = document.createElement("li");
      li.textContent = `${item.title} (${item.type})`;
      ul.appendChild(li);
    });
    resultDiv.appendChild(ul);
  } catch (error) {
    resultDiv.innerHTML = "❌ حصل خطأ أثناء الاتصال بالـ AI.";
  }
}
