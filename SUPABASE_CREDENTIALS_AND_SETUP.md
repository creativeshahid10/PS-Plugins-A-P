# 🚀 PixelSquad Supabase Complete Setup, Automation & Student Whitelist Guide

**Author:** Mohammed Shahid  
**Email:** hello@pixelsquad.in  
**Location:** `E:\PixelSquad\Classes\Plugins`  

---

## 1. Do (2) Credentials Jo Aapko Copy Karne Hain:

Supabase Dashboard ([supabase.com](https://supabase.com)) mein apna project open karein, aur left sidebar mein:
👉 **Project Settings (Gear Icon) -> API** par jayein:

1. **Project URL**:  
   Format: `https://abcdefghijklm.supabase.co`
2. **Project API Key (`anon` / `public`)**:  
   Format: `eyJhbGciOi...` (lamba text token)

---

## 2. Supabase SQL Editor Mein 1-Click Code (Copy-Paste & Run):

Supabase ke left menu mein **SQL Editor** par click karein aur yeh poora script paste karke **RUN** daba dein:

```sql
-- ======================================================================
-- 1. LICENSES TABLE (For Commercial Buyers)
-- ======================================================================
CREATE TABLE IF NOT EXISTS public.pixelsquad_licenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    license_key TEXT UNIQUE NOT NULL,
    buyer_name TEXT NOT NULL,
    buyer_email TEXT NOT NULL,
    product TEXT DEFAULT 'PixelSquad Master Suite 2026',
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'revoked', 'expired')),
    max_devices INT DEFAULT 1,
    activated_devices JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_verified_at TIMESTAMP WITH TIME ZONE
);

-- ======================================================================
-- 2. STUDENT WHITELIST TABLE (For Free Student Access)
-- ======================================================================
CREATE TABLE IF NOT EXISTS public.pixelsquad_students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_email TEXT UNIQUE NOT NULL,
    student_name TEXT NOT NULL,
    batch_name TEXT DEFAULT 'PixelSquad Academy',
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'suspended')),
    activated_devices JSONB DEFAULT '[]'::jsonb,
    max_devices INT DEFAULT 2, -- Students can use on laptop + desktop
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE
);

-- Sample Student (Aap testing ke liye use kar sakte hain)
INSERT INTO public.pixelsquad_students (student_email, student_name, batch_name)
VALUES ('student@pixelsquad.in', 'Demo Student', 'Batch 2026')
ON CONFLICT (student_email) DO NOTHING;

-- ======================================================================
-- 3. TELEMETRY TABLE (Live Active / Inactive Laptops Tracking)
-- ======================================================================
CREATE TABLE IF NOT EXISTS public.pixelsquad_telemetry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    machine_id TEXT NOT NULL,
    license_key TEXT,
    event TEXT, -- 'trial_started', 'heartbeat', 'app_open'
    platform TEXT,
    last_ping TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ======================================================================
-- 4. UNIFIED ACTIVATION RPC FUNCTION (Handles Buyers + Students + Kill Switch)
-- ======================================================================
CREATE OR REPLACE FUNCTION public.activate_pixelsquad_license(
    p_license_key TEXT,
    p_email TEXT,
    p_machine_id TEXT,
    p_machine_name TEXT,
    p_is_student BOOLEAN DEFAULT FALSE
) RETURNS JSONB LANGUAGE plpgsql SECURITY DEFINER AS $$
DECLARE
    v_student RECORD;
    v_lic RECORD;
    v_devices JSONB;
BEGIN
    -- [A] CHECK STUDENT WHITELIST
    IF p_is_student = TRUE OR LOWER(p_license_key) = 'student_free' THEN
        SELECT * INTO v_student FROM public.pixelsquad_students 
        WHERE LOWER(student_email) = LOWER(p_email);

        IF NOT FOUND THEN
            RETURN jsonb_build_object('success', false, 'message', 'Student email not found in whitelist. Contact PixelSquad Admin.');
        END IF;

        IF v_student.status != 'active' THEN
            RETURN jsonb_build_object('success', false, 'message', 'Student account is ' || v_student.status || '. Contact support.');
        END IF;

        v_devices := v_student.activated_devices;

        -- Check if machine already registered
        IF v_devices @> jsonb_build_array(jsonb_build_object('machine_id', p_machine_id)) THEN
            UPDATE public.pixelsquad_students SET last_login_at = NOW() WHERE id = v_student.id;
            RETURN jsonb_build_object('success', true, 'message', 'Welcome back, ' || v_student.student_name || '!', 'buyer', v_student.student_name, 'tier', 'STUDENT');
        END IF;

        -- Check device limit
        IF jsonb_array_length(v_devices) >= v_student.max_devices THEN
            RETURN jsonb_build_object('success', false, 'message', 'Student device limit reached (Max ' || v_student.max_devices || ' devices).');
        END IF;

        -- Register student machine
        v_devices := v_devices || jsonb_build_object('machine_id', p_machine_id, 'device_name', p_machine_name, 'activated_at', NOW());
        UPDATE public.pixelsquad_students 
        SET activated_devices = v_devices, last_login_at = NOW() 
        WHERE id = v_student.id;

        RETURN jsonb_build_object('success', true, 'message', 'Welcome PixelSquad Student: ' || v_student.student_name || '!', 'buyer', v_student.student_name, 'tier', 'STUDENT');
    END IF;

    -- [B] CHECK COMMERCIAL LICENSE KEY
    SELECT * INTO v_lic FROM public.pixelsquad_licenses 
    WHERE license_key = p_license_key;

    IF NOT FOUND THEN
        RETURN jsonb_build_object('success', false, 'message', 'Invalid License Key.');
    END IF;

    IF v_lic.status != 'active' THEN
        RETURN jsonb_build_object('success', false, 'message', 'License is ' || v_lic.status || '. Contact hello@pixelsquad.in');
    END IF;

    v_devices := v_lic.activated_devices;

    IF v_devices @> jsonb_build_array(jsonb_build_object('machine_id', p_machine_id)) THEN
        UPDATE public.pixelsquad_licenses SET last_verified_at = NOW() WHERE id = v_lic.id;
        RETURN jsonb_build_object('success', true, 'message', 'Device verified.', 'buyer', v_lic.buyer_name, 'tier', 'COMMERCIAL');
    END IF;

    IF jsonb_array_length(v_devices) >= v_lic.max_devices THEN
        RETURN jsonb_build_object('success', false, 'message', 'Activation limit reached (Max ' || v_lic.max_devices || ' PC).');
    END IF;

    v_devices := v_devices || jsonb_build_object('machine_id', p_machine_id, 'device_name', p_machine_name, 'activated_at', NOW());
    UPDATE public.pixelsquad_licenses 
    SET activated_devices = v_devices, last_verified_at = NOW() 
    WHERE id = v_lic.id;

    RETURN jsonb_build_object('success', true, 'message', 'License activated successfully!', 'buyer', v_lic.buyer_name, 'tier', 'COMMERCIAL');
END;
$$;

-- Grant public API permissions
GRANT EXECUTE ON FUNCTION public.activate_pixelsquad_license TO anon;
GRANT INSERT ON public.pixelsquad_telemetry TO anon;
```

---

## 3. Website Se Purchase Hone Par Key Kaise Bheji Jayegi?

Aapne poocha: *"Yeh Supabase bhejega ki hamara web application bhejega?"*

### Clear Flow:
1. **Buyer Purchase**: Customer aapki website (jaise `workshops.pixelsquad.in` ya `pixelsquad.in`) par Razorpay / Stripe se payment karta hai.
2. **Website Backend Generates Key**: Payment successful hote hi aapki website ka backend ek unique key generate karta hai:
   ```javascript
   // Example in Next.js / Node API:
   const licenseKey = "PS-2026-" + Math.random().toString(36).substr(2, 6).toUpperCase() + "-" + Math.random().toString(36).substr(2, 6).toUpperCase();
   
   // Insert into Supabase
   await supabase.from('pixelsquad_licenses').insert({
       license_key: licenseKey,
       buyer_name: customerName,
       buyer_email: customerEmail,
       max_devices: 1
   });
   ```
3. **Automated Email**: Aapki website (via Resend, Sendgrid ya Nodemailer) turant buyer ko automated branded email send kar degi:
   - *"Dear [Name], thank you for purchasing PixelSquad Master Suite! Your License Key is: PS-2026-XXXX-XXXX. Download link: [link]"*
4. **Student Whitelist**: Aapko bas Supabase dashboard mein jaakar `pixelsquad_students` table mein student ka email aur naam add kar dena hai (ya CSV import kar dena hai). Student direct extension mein apna email daal kar bina kisi key ke 100% free access le sakega!
