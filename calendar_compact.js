// Compact Modern Calendar Implementation
// Copy this into admin.html to replace the loadCalendar function

async function loadCalendar() {
    try {
        const response = await fetch('/api/appointments', {
            headers: getAuthHeaders()
        });
        const data = await response.json();
        const appointments = data.appointments || [];
        const now = new Date();

        // Render based on current view
        if (currentCalendarView === 'day') {
            renderDayView(appointments, now);
        } else if (currentCalendarView === 'week') {
            renderWeekView(appointments, now);
        } else {
            renderMonthView(appointments, now);
        }

        // Scroll to target appointment if exists
        if (targetAppointmentId !== null) {
            setTimeout(() => {
                const targetElement = document.querySelector('.flicker-target');
                if (targetElement) {
                    targetElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }, 100);
            targetAppointmentId = null;
        }
    } catch (error) {
        console.error('Failed to load calendar:', error);
        document.getElementById('calendarGrid').innerHTML = '<div style="padding: 40px; text-align: center; color: rgba(255,255,255,0.5);">Error loading calendar</div>';
    }
}

function renderDayView(appointments, now) {
    const currentDate = new Date(now);
    currentDate.setDate(now.getDate() + currentDayOffset);
    const dateStr = currentDate.toISOString().split('T')[0];
    
    const dayName = currentDate.toLocaleDateString('en-US', { weekday: 'long' });
    const monthYear = currentDate.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
    
    document.getElementById('currentMonthDisplay').textContent = `${dayName}, ${monthYear}`;

    const dayAppointments = appointments.filter(apt => apt.date === dateStr);
    const isToday = dateStr === now.toISOString().split('T')[0];

    let html = '<div style="display: grid; grid-template-columns: 60px 1fr; gap: 1px; background: rgba(255,255,255,0.05); border-radius: 12px; overflow: hidden;">';

    // Time slots (6 AM to 10 PM for day view)
    for (let hour = 6; hour <= 22; hour++) {
        const timeStr = `${String(hour).padStart(2, '0')}:00`;
        const slotAppointments = dayAppointments.filter(apt => {
            const aptHour = parseInt(apt.time.split(':')[0]);
            return aptHour === hour;
        });

        // Time label
        html += `<div style="background: rgba(0,0,0,0.4); padding: 12px 8px; text-align: right; font-size: 11px; font-weight: 700; color: rgba(255,255,255,0.5); border-bottom: 1px solid rgba(255,255,255,0.05);">${timeStr}</div>`;
        
        // Content cell
        html += `<div onclick="showTimeSlot('${dateStr}', '${timeStr}')" style="background: ${isToday ? 'rgba(102,126,234,0.08)' : 'rgba(0,0,0,0.2)'}; padding: 12px; min-height: 50px; cursor: pointer; transition: all 0.2s; border-bottom: 1px solid rgba(255,255,255,0.05);" onmouseover="this.style.background='rgba(102,126,234,0.15)'" onmouseout="this.style.background='${isToday ? 'rgba(102,126,234,0.08)' : 'rgba(0,0,0,0.2)'}'">`;
        
        slotAppointments.forEach(apt => {
            const emoji = apt.status === 'busy' ? '🚫' : apt.status === 'completed' ? '✅' : '📅';
            const bgColor = apt.status === 'busy' ? 'rgba(255,100,100,0.5)' : apt.created_by === 'ai_agent' ? 'rgba(100,200,255,0.5)' : 'rgba(102,126,234,0.7)';
            const isTarget = targetAppointmentId !== null && apt.id === targetAppointmentId;
            
            html += `<div onclick="event.stopPropagation(); viewAppointment(${apt.id})" class="${isTarget ? 'flicker-target' : ''}" style="background: ${bgColor}; padding: 10px 12px; border-radius: 8px; margin-bottom: 6px; font-size: 12px; font-weight: 600; border-left: 4px solid rgba(255,255,255,0.6); cursor: pointer; transition: all 0.2s; box-shadow: 0 2px 8px rgba(0,0,0,0.2);" onmouseover="this.style.transform='translateX(4px)'; this.style.boxShadow='0 4px 12px rgba(0,0,0,0.3)'" onmouseout="this.style.transform='translateX(0)'; this.style.boxShadow='0 2px 8px rgba(0,0,0,0.2)'">`;
            html += `<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">`;
            html += `<span style="font-size: 16px;">${emoji}</span>`;
            html += `<span style="font-weight: 700;">${apt.time} ${apt.title || 'Appointment'}</span>`;
            html += `</div>`;
            if (apt.customer_name) {
                html += `<div style="font-size: 11px; color: rgba(255,255,255,0.9); margin-left: 24px;">👤 ${apt.customer_name}</div>`;
            }
            if (apt.description) {
                html += `<div style="font-size: 10px; color: rgba(255,255,255,0.7); margin-left: 24px; margin-top: 4px;">${apt.description}</div>`;
            }
            html += `</div>`;
        });
        
        html += '</div>';
    }

    html += '</div>';
    document.getElementById('calendarGrid').innerHTML = html;
}

function renderWeekView(appointments, now) {
    const currentDay = now.getDay();
    const weekStart = new Date(now);
    weekStart.setDate(now.getDate() - currentDay + (currentWeekOffset * 7));

    const weekMiddle = new Date(weekStart);
    weekMiddle.setDate(weekStart.getDate() + 3);
    const monthYear = weekMiddle.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
    
    document.getElementById('currentMonthDisplay').textContent = monthYear;

    const dayNames = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
    let html = '<div style="display: flex; flex-direction: column;">';
    
    // Compact header
    html += '<div style="display: grid; grid-template-columns: 60px repeat(7, 1fr); gap: 1px; background: rgba(255,255,255,0.08); border-radius: 10px; overflow: hidden; margin-bottom: 2px;">';
    html += '<div style="background: rgba(102,126,234,0.25); padding: 10px; text-align: center; font-weight: 700;"></div>';
    
    for (let i = 0; i < 7; i++) {
        const date = new Date(weekStart);
        date.setDate(weekStart.getDate() + i);
        const dateStr = date.toISOString().split('T')[0];
        const isToday = dateStr === now.toISOString().split('T')[0];
        
        html += `<div style="background: ${isToday ? 'linear-gradient(135deg, rgba(102,126,234,0.5), rgba(118,75,162,0.5))' : 'rgba(102,126,234,0.25)'}; padding: 10px; text-align: center;">`;
        html += `<div style="font-weight: 800; font-size: 10px; color: ${isToday ? '#fff' : 'rgba(255,255,255,0.6)'};">${dayNames[i]}</div>`;
        html += `<div style="font-size: 20px; font-weight: 900; margin-top: 2px;">${date.getDate()}</div>`;
        html += `</div>`;
    }
    html += '</div>';

    // Compact time slots (8 AM to 6 PM)
    html += '<div style="display: grid; grid-template-columns: 60px repeat(7, 1fr); gap: 1px; background: rgba(255,255,255,0.03);">';
    
    for (let hour = 8; hour <= 18; hour++) {
        const timeStr = `${String(hour).padStart(2, '0')}:00`;
        
        html += `<div style="background: rgba(0,0,0,0.3); padding: 12px 6px; text-align: right; font-size: 10px; font-weight: 700; color: rgba(255,255,255,0.5); border-bottom: 1px solid rgba(255,255,255,0.05);">${timeStr}</div>`;
        
        for (let i = 0; i < 7; i++) {
            const date = new Date(weekStart);
            date.setDate(weekStart.getDate() + i);
            const dateStr = date.toISOString().split('T')[0];
            
            const slotAppointments = appointments.filter(apt => {
                if (apt.date !== dateStr) return false;
                const aptHour = parseInt(apt.time.split(':')[0]);
                return aptHour === hour;
            });
            
            const isToday = dateStr === now.toISOString().split('T')[0];
            
            html += `<div onclick="showTimeSlot('${dateStr}', '${timeStr}')" style="background: ${isToday ? 'rgba(102,126,234,0.08)' : 'rgba(0,0,0,0.2)'}; padding: 6px 4px; min-height: 45px; cursor: pointer; transition: all 0.2s; border-bottom: 1px solid rgba(255,255,255,0.05);" onmouseover="this.style.background='rgba(102,126,234,0.15)'" onmouseout="this.style.background='${isToday ? 'rgba(102,126,234,0.08)' : 'rgba(0,0,0,0.2)'}'">`;
            
            slotAppointments.forEach(apt => {
                const emoji = apt.status === 'busy' ? '🚫' : apt.status === 'completed' ? '✅' : '📅';
                const bgColor = apt.status === 'busy' ? 'rgba(255,100,100,0.5)' : apt.created_by === 'ai_agent' ? 'rgba(100,200,255,0.5)' : 'rgba(102,126,234,0.7)';
                const isTarget = targetAppointmentId !== null && apt.id === targetAppointmentId;
                
                html += `<div onclick="event.stopPropagation(); viewAppointment(${apt.id})" class="${isTarget ? 'flicker-target' : ''}" style="background: ${bgColor}; padding: 4px 6px; border-radius: 6px; margin-bottom: 3px; font-size: 10px; font-weight: 600; border-left: 3px solid rgba(255,255,255,0.5); cursor: pointer; transition: all 0.2s;" onmouseover="this.style.transform='scale(1.03)'" onmouseout="this.style.transform='scale(1)'">`;
                html += `<div style="display: flex; align-items: center; gap: 3px;">`;
                html += `<span style="font-size: 11px;">${emoji}</span>`;
                html += `<span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 10px;">${apt.time.slice(0,5)} ${apt.title || 'Appt'}</span>`;
                html += `</div>`;
                html += `</div>`;
            });
            
            html += '</div>';
        }
    }
    
    html += '</div></div>';
    document.getElementById('calendarGrid').innerHTML = html;
}

function renderMonthView(appointments, now) {
    const currentDate = new Date(now);
    currentDate.setDate(1); // First day of month
    currentDate.setMonth(now.getMonth() + Math.floor(currentWeekOffset / 4));
    
    const monthYear = currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
    document.getElementById('currentMonthDisplay').textContent = monthYear;

    const firstDay = currentDate.getDay();
    const daysInMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0).getDate();
    
    let html = '<div style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; background: rgba(255,255,255,0.05); border-radius: 12px; overflow: hidden; padding: 2px;">';
    
    // Day names header
    const dayNames = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
    dayNames.forEach(day => {
        html += `<div style="background: rgba(102,126,234,0.25); padding: 12px; text-align: center; font-weight: 800; font-size: 11px; color: rgba(255,255,255,0.7);">${day}</div>`;
    });
    
    // Empty cells before first day
    for (let i = 0; i < firstDay; i++) {
        html += '<div style="background: rgba(0,0,0,0.2); padding: 12px; min-height: 90px;"></div>';
    }
    
    // Days of month
    for (let day = 1; day <= daysInMonth; day++) {
        const date = new Date(currentDate.getFullYear(), currentDate.getMonth(), day);
        const dateStr = date.toISOString().split('T')[0];
        const isToday = dateStr === now.toISOString().split('T')[0];
        
        const dayAppointments = appointments.filter(apt => apt.date === dateStr);
        
        html += `<div onclick="currentDayOffset = ${Math.floor((date - now) / (1000 * 60 * 60 * 24))}; switchView('day');" style="background: ${isToday ? 'linear-gradient(135deg, rgba(102,126,234,0.3), rgba(118,75,162,0.3))' : 'rgba(0,0,0,0.2)'}; padding: 8px; min-height: 90px; cursor: pointer; transition: all 0.2s; border: ${isToday ? '2px solid rgba(102,126,234,0.6)' : '1px solid rgba(255,255,255,0.05)'}; border-radius: 8px;" onmouseover="this.style.background='rgba(102,126,234,0.2)'" onmouseout="this.style.background='${isToday ? 'linear-gradient(135deg, rgba(102,126,234,0.3), rgba(118,75,162,0.3))' : 'rgba(0,0,0,0.2)'}'">`;
        html += `<div style="font-weight: 900; font-size: 16px; margin-bottom: 6px; color: ${isToday ? '#fff' : 'rgba(255,255,255,0.8)'};">${day}</div>`;
        
        dayAppointments.slice(0, 3).forEach(apt => {
            const emoji = apt.status === 'busy' ? '🚫' : apt.status === 'completed' ? '✅' : '📅';
            const bgColor = apt.status === 'busy' ? 'rgba(255,100,100,0.6)' : apt.created_by === 'ai_agent' ? 'rgba(100,200,255,0.6)' : 'rgba(102,126,234,0.8)';
            
            html += `<div onclick="event.stopPropagation(); viewAppointment(${apt.id})" style="background: ${bgColor}; padding: 4px 6px; border-radius: 5px; margin-bottom: 3px; font-size: 9px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; transition: all 0.2s;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">`;
            html += `${emoji} ${apt.time.slice(0,5)} ${apt.title || 'Appt'}`;
            html += `</div>`;
        });
        
        if (dayAppointments.length > 3) {
            html += `<div style="font-size: 9px; color: rgba(255,255,255,0.6); font-weight: 600; margin-top: 3px;">+${dayAppointments.length - 3} more</div>`;
        }
        
        html += '</div>';
    }
    
    html += '</div>';
    document.getElementById('calendarGrid').innerHTML = html;
}
