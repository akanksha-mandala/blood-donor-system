const BASE_URL = "http://127.0.0.1:5000";

// -----------------------------
// Aadhaar Validation
// -----------------------------
function validateAadhaar(aadhaar) {
    return /^\d{12}$/.test(aadhaar);
}

function setAadhaarStatus(inputId, statusId, helperId) {
    const input = document.getElementById(inputId);
    const status = document.getElementById(statusId);
    const helper = document.getElementById(helperId);

    if (!input || !status || !helper) return;

    input.addEventListener("input", () => {
        const value = input.value.trim();

        if (!value) {
            status.classList.add("hidden");
            helper.textContent = "";
            return;
        }

        if (validateAadhaar(value)) {
            status.classList.remove("hidden");
            status.textContent = "Valid format";
            status.className = "absolute right-3 top-1/2 -translate-y-1/2 text-xs font-semibold text-blue-600";
            helper.textContent = "Format valid. Government identity still needs verification.";
        } else {
            status.classList.add("hidden");
            helper.textContent = "Aadhaar must contain exactly 12 digits.";
        }
    });
}

function setupAadhaarValidation() {
    setAadhaarStatus("aadhaar_number", "aadhaar-donor-status", "aadhaar-donor-helper");
    setAadhaarStatus("r_aadhaar_number", "aadhaar-recipient-status", "aadhaar-recipient-helper");
}

// -----------------------------
// Get Coordinates
// -----------------------------
async function getCoordinates(city) {
    const res = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(city)}`
    );

    const data = await res.json();

    if (!data.length) throw new Error("City not found");

    return {
        latitude: parseFloat(data[0].lat),
        longitude: parseFloat(data[0].lon)
    };
}

// -----------------------------
// Donor Registration (FormData)
// -----------------------------
async function handleDonorRegistration() {
    try {
        const city = document.getElementById("city").value.trim();
        const coords = await getCoordinates(city);
        const aadhaar = document.getElementById("aadhaar_number").value.trim();

        if (!validateAadhaar(aadhaar)) {
            alert("Aadhaar must be exactly 12 digits");
            return;
        }

        const profileImage = document.getElementById("profile_image")?.files?.[0];
        const aadhaarProof = document.getElementById("aadhaar_proof_file")?.files?.[0];

        if (!profileImage || !aadhaarProof) {
            alert("Profile image and Aadhaar proof are required");
            return;
        }

        const formData = new FormData();
        formData.append("full_name", document.getElementById("full_name").value.trim());
        formData.append("age", document.getElementById("age").value.trim());
        formData.append("email", document.getElementById("email").value.trim());
        formData.append("phone", document.getElementById("phone").value.trim());
        formData.append("aadhaar_number", aadhaar);
        formData.append("blood_group", document.getElementById("blood_group").value);
        formData.append("city", city);
        formData.append("latitude", coords.latitude);
        formData.append("longitude", coords.longitude);
        formData.append("profile_image", profileImage);
        formData.append("aadhaar_proof_file", aadhaarProof);

        const res = await fetch(`${BASE_URL}/api/donors/register`, {
            method: "POST",
            body: formData
        });

        const result = await res.json();
        alert(result.message);

        if (res.ok && result.verified_badge) {
            document.getElementById("donor-verify-badge")?.classList.remove("hidden");
        }

        if (res.ok) {
            loadVerifiedRequests();
            loadVerifiedDonors();
            document.getElementById("donor-form")?.reset();
        }

    } catch (err) {
        console.error(err);
        alert("Donor registration failed");
    }
}

// -----------------------------
// Recipient Registration (FormData)
// -----------------------------
async function handleRecipientRegistration() {
    try {
        const city = document.getElementById("r_city").value.trim();
        const coords = await getCoordinates(city);
        const aadhaar = document.getElementById("r_aadhaar_number").value.trim();

        if (!validateAadhaar(aadhaar)) {
            alert("Aadhaar must be exactly 12 digits");
            return;
        }

        const profileImage = document.getElementById("r_profile_image")?.files?.[0];
        const aadhaarProof = document.getElementById("r_aadhaar_proof_file")?.files?.[0];

        if (!profileImage || !aadhaarProof) {
            alert("Profile image and Aadhaar proof are required");
            return;
        }

        const formData = new FormData();
        formData.append("full_name", document.getElementById("r_full_name").value.trim());
        formData.append("phone", document.getElementById("r_phone").value.trim());
        formData.append("email", document.getElementById("r_email").value.trim());
        formData.append("aadhaar_number", aadhaar);
        formData.append("blood_group_needed", document.getElementById("r_blood_group_needed").value);
        formData.append("city", city);
        formData.append("hospital_name", document.getElementById("hospital_name").value.trim());
        formData.append("hospital_address", document.getElementById("hospital_address").value.trim());
        formData.append("doctor_name", document.getElementById("doctor_name").value.trim());
        formData.append("attender_name", document.getElementById("attender_name").value.trim());
        formData.append("attender_phone", document.getElementById("attender_phone").value.trim());
        formData.append("latitude", coords.latitude);
        formData.append("longitude", coords.longitude);
        formData.append("radius_km", document.getElementById("search_radius")?.value || 30);
        formData.append("profile_image", profileImage);
        formData.append("aadhaar_proof_file", aadhaarProof);

        const res = await fetch(`${BASE_URL}/api/recipients/register`, {
            method: "POST",
            body: formData
        });

        const result = await res.json();
        alert(result.message);

        if (res.ok && result.verification_status === "verified") {
            document.getElementById("recipient-verify-badge")?.classList.remove("hidden");
        }

        if (res.ok) {
            document.getElementById("recipient-form")?.reset();
        }

    } catch (err) {
        console.error(err);
        alert("Recipient request failed");
    }
}

// -----------------------------
// Verified Requests
// -----------------------------
async function loadVerifiedRequests() {
    try {
        const res = await fetch(`${BASE_URL}/api/donors/verified-requests`);
        const requests = await res.json();

        const feed = document.getElementById("requests-feed");
        if (!feed) return;

        if (!requests.length) {
            feed.innerHTML = `<p class="text-gray-500">No verified requests available.</p>`;
            return;
        }

        feed.innerHTML = requests.map(req => `
            <div class="bg-white p-4 rounded-lg shadow border mb-3">
                <div class="flex justify-between mb-2">
                    <span class="font-bold text-red-600">${req.blood_group_needed}</span>
                    <span class="text-xs px-2 py-1 bg-green-100 text-green-700 rounded-full">
                        VERIFIED
                    </span>
                </div>

                <p><strong>Hospital:</strong> ${req.hospital_name || "N/A"}</p>
                <p><strong>Address:</strong> ${req.hospital_address || "N/A"}</p>
                <p><strong>Doctor:</strong> ${req.doctor_name || "N/A"}</p>
                <p><strong>City:</strong> ${req.city || "N/A"}</p>
            </div>
        `).join("");

    } catch (err) {
        console.error(err);
    }
}

// -----------------------------
// Verified Donors UI
// -----------------------------
async function loadVerifiedDonors() {
    try {
        const res = await fetch(`${BASE_URL}/api/donors/verified-list`);
        const donors = await res.json();

        const feed = document.getElementById("verified-donors-feed");
        if (!feed) return;

        if (!donors.length) {
            feed.innerHTML = `<p class="text-gray-500 italic col-span-full">No verified donors available yet...</p>`;
            return;
        }

        feed.innerHTML = donors.map(donor => `
            <div class="bg-gray-50 border rounded-xl p-4 shadow-sm">
                <div class="flex items-start gap-3">
                    <img
                        src="${donor.profile_image || 'https://via.placeholder.com/56?text=U'}"
                        alt="${donor.full_name}"
                        class="w-14 h-14 rounded-full object-cover border"
                    />
                    <div class="flex-1">
                        <div class="flex items-center justify-between mb-1">
                            <div class="font-semibold text-gray-800">${donor.full_name}</div>
                            <span class="text-xs px-2 py-1 bg-green-100 text-green-700 rounded-full">
                                Verified ✓
                            </span>
                        </div>
                        <p class="text-sm text-gray-600"><strong>Blood Group:</strong> ${donor.blood_group}</p>
                        <p class="text-sm text-gray-600"><strong>City:</strong> ${donor.city}</p>
                        <p class="text-sm text-gray-600"><strong>Donations:</strong> ${donor.donation_count}</p>
                    </div>
                </div>
            </div>
        `).join("");

    } catch (err) {
        console.error(err);
    }
}

// -----------------------------
// Admin Dashboard
// -----------------------------
async function loadAdminDashboard() {
    await Promise.all([
        loadPendingDonors(),
        loadPendingRecipients(),
        loadPendingRequests(),
        loadBlockedUsers()
    ]);
}

// -----------------------------
async function loadPendingDonors() {
    try {
        const res = await fetch(`${BASE_URL}/api/admin/donors/pending`);
        const donors = await res.json();

        const box = document.getElementById("pending-donors");
        if (!box) return;

        box.innerHTML = donors.length
            ? donors.map(d => `
                <div class="border p-3 rounded mb-2 bg-gray-50">
                    <div class="flex gap-3">
                        <img
                            src="${d.profile_image ? `${BASE_URL.replace('/api','')}/uploads/${d.profile_image}` : 'https://via.placeholder.com/56?text=U'}"
                            alt="${d.full_name}"
                            class="w-14 h-14 rounded-full object-cover border"
                        />
                        <div class="flex-1">
                            <p class="font-semibold">${d.full_name}</p>
                            <p class="text-sm text-gray-600">${d.blood_group} • ${d.city}</p>
                            <p class="text-sm text-gray-500">${d.aadhaar_masked || ""}</p>
                            <p class="text-xs text-gray-500 mt-1">Source: ${d.verification_source || "manual_review"}</p>

                            ${d.aadhaar_proof_file ? `
                                <a
                                    href="${BASE_URL.replace('/api','')}/uploads/${d.aadhaar_proof_file}"
                                    target="_blank"
                                    class="inline-block mt-2 text-sm text-blue-600 underline"
                                >
                                    View Aadhaar Proof
                                </a>
                            ` : ""}
                        </div>
                    </div>

                    <div class="mt-3 flex gap-2">
                        <button onclick="verifyDonor(${d.id})"
                            class="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700">
                            Verify
                        </button>

                        <button onclick="rejectDonor(${d.id})"
                            class="px-3 py-1 bg-yellow-500 text-white rounded hover:bg-yellow-600">
                            Reject
                        </button>

                        <button onclick="blockDonor(${d.id})"
                            class="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700">
                            Block
                        </button>
                    </div>
                </div>
            `).join("")
            : "No pending donors";

    } catch (err) {
        console.error(err);
    }
}

// -----------------------------
async function loadPendingRecipients() {
    try {
        const res = await fetch(`${BASE_URL}/api/admin/recipients/pending`);
        const recipients = await res.json();

        const box = document.getElementById("pending-recipients");
        if (!box) return;

        box.innerHTML = recipients.length
            ? recipients.map(r => `
                <div class="border p-3 rounded mb-2 bg-gray-50">
                    <div class="flex gap-3">
                        <img
                            src="${r.profile_image ? `${BASE_URL.replace('/api','')}/uploads/${r.profile_image}` : 'https://via.placeholder.com/56?text=U'}"
                            alt="${r.full_name}"
                            class="w-14 h-14 rounded-full object-cover border"
                        />
                        <div class="flex-1">
                            <p class="font-semibold">${r.full_name}</p>
                            <p class="text-sm text-gray-600">${r.blood_group_needed} • ${r.city}</p>
                            <p class="text-sm text-gray-500">${r.hospital_name || ""}</p>
                            <p class="text-sm text-gray-500">${r.aadhaar_masked || ""}</p>
                            <p class="text-xs text-gray-500 mt-1">Source: ${r.verification_source || "manual_review"}</p>

                            ${r.aadhaar_proof_file ? `
                                <a
                                    href="${BASE_URL.replace('/api','')}/uploads/${r.aadhaar_proof_file}"
                                    target="_blank"
                                    class="inline-block mt-2 text-sm text-blue-600 underline"
                                >
                                    View Aadhaar Proof
                                </a>
                            ` : ""}
                        </div>
                    </div>

                    <div class="mt-3 flex gap-2">
                        <button onclick="verifyRecipient(${r.id})"
                            class="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700">
                            Verify
                        </button>

                        <button onclick="rejectRecipient(${r.id})"
                            class="px-3 py-1 bg-yellow-500 text-white rounded hover:bg-yellow-600">
                            Reject
                        </button>

                        <button onclick="blockRecipient(${r.id})"
                            class="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700">
                            Block
                        </button>
                    </div>
                </div>
            `).join("")
            : "No pending recipients";

    } catch (err) {
        console.error(err);
    }
}

// -----------------------------
async function loadPendingRequests() {
    try {
        const res = await fetch(`${BASE_URL}/api/admin/requests/pending`);
        const requests = await res.json();

        const box = document.getElementById("pending-requests");
        if (!box) return;

        box.innerHTML = requests.length
            ? requests.map(r => `
                <div class="border p-3 rounded mb-2 bg-gray-50">
                    <p class="font-semibold">Request #${r.id}</p>
                    <p class="text-sm text-gray-600">${r.blood_group_needed} • ${r.city}</p>
                    <p class="text-sm text-gray-500">${r.hospital_name || ""}</p>

                    <div class="mt-3 flex gap-2">
                        <button onclick="verifyRequest(${r.id})"
                            class="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700">
                            Verify Request
                        </button>

                        <button onclick="rejectRequest(${r.id})"
                            class="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700">
                            Reject
                        </button>
                    </div>
                </div>
            `).join("")
            : "No pending requests";

    } catch (err) {
        console.error(err);
    }
}

// -----------------------------
async function loadBlockedUsers() {
    try {
        const res = await fetch(`${BASE_URL}/api/admin/fraud-blocked`);
        const data = await res.json();

        const box = document.getElementById("blocked-users");
        if (!box) return;

        const blockedDonors = data.blocked_donors || [];
        const blockedRecipients = data.blocked_recipients || [];

        if (!blockedDonors.length && !blockedRecipients.length) {
            box.innerHTML = "No blocked accounts yet.";
            return;
        }

        box.innerHTML = `
            ${blockedDonors.map(d => `
                <div class="border p-3 rounded mb-2 bg-red-50">
                    <p class="font-semibold">Donor: ${d.full_name}</p>
                    <p class="text-sm text-gray-600">${d.blood_group} • ${d.city}</p>
                </div>
            `).join("")}
            ${blockedRecipients.map(r => `
                <div class="border p-3 rounded mb-2 bg-red-50">
                    <p class="font-semibold">Recipient: ${r.full_name}</p>
                    <p class="text-sm text-gray-600">${r.blood_group_needed} • ${r.city}</p>
                </div>
            `).join("")}
        `;

    } catch (err) {
        console.error(err);
    }
}

// -----------------------------
async function verifyDonor(id) {
    const res = await fetch(`${BASE_URL}/api/admin/donors/${id}/verify`, {
        method: "POST"
    });
    const result = await res.json();
    alert(result.message);
    loadAdminDashboard();
    loadVerifiedDonors();
}

// -----------------------------
async function rejectDonor(id) {
    const res = await fetch(`${BASE_URL}/api/admin/donors/${id}/reject`, {
        method: "POST"
    });
    const result = await res.json();
    alert(result.message);
    loadAdminDashboard();
}

// -----------------------------
async function blockDonor(id) {
    const res = await fetch(`${BASE_URL}/api/admin/donors/${id}/block`, {
        method: "POST"
    });
    const result = await res.json();
    alert(result.message);
    loadAdminDashboard();
}

// -----------------------------
async function verifyRecipient(id) {
    const res = await fetch(`${BASE_URL}/api/admin/recipients/${id}/verify`, {
        method: "POST"
    });
    const result = await res.json();
    alert(result.message);
    loadAdminDashboard();
}

// -----------------------------
async function rejectRecipient(id) {
    const res = await fetch(`${BASE_URL}/api/admin/recipients/${id}/reject`, {
        method: "POST"
    });
    const result = await res.json();
    alert(result.message);
    loadAdminDashboard();
}

// -----------------------------
async function blockRecipient(id) {
    const res = await fetch(`${BASE_URL}/api/admin/recipients/${id}/flag-scam`, {
        method: "POST"
    });
    const result = await res.json();
    alert(result.message);
    loadAdminDashboard();
}

// -----------------------------
async function verifyRequest(id) {
    const res = await fetch(`${BASE_URL}/api/admin/requests/${id}/verify`, {
        method: "POST"
    });
    const result = await res.json();
    alert(result.message);
    loadAdminDashboard();
    loadVerifiedRequests();
}

// -----------------------------
async function rejectRequest(id) {
    const res = await fetch(`${BASE_URL}/api/admin/requests/${id}/reject`, {
        method: "POST"
    });
    const result = await res.json();
    alert(result.message);
    loadAdminDashboard();
}

// -----------------------------
window.setupAadhaarValidation = setupAadhaarValidation;
window.handleDonorRegistration = handleDonorRegistration;
window.handleRecipientRegistration = handleRecipientRegistration;
window.loadVerifiedRequests = loadVerifiedRequests;
window.loadVerifiedDonors = loadVerifiedDonors;
window.loadAdminDashboard = loadAdminDashboard;

window.verifyDonor = verifyDonor;
window.rejectDonor = rejectDonor;
window.blockDonor = blockDonor;

window.verifyRecipient = verifyRecipient;
window.rejectRecipient = rejectRecipient;
window.blockRecipient = blockRecipient;

window.verifyRequest = verifyRequest;
window.rejectRequest = rejectRequest;