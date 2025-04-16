-- SteadwellOS Palliative Care Platform
-- WORKING DATABASE BACKUP
-- Created: Tue Apr 15 19:04:00 PDT 2025
-- This is a known working backup for use in Quome Cloud environment
-- Format tweaked to avoid ownership issues

--
-- PostgreSQL database dump
--

-- Dumped from database version 14.17 (Debian 14.17-1.pgdg120+1)
-- Dumped by pg_dump version 14.17 (Debian 14.17-1.pgdg120+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: callstatus; Type: TYPE; Schema: public; Owner: pallcare
--

CREATE TYPE public.callstatus AS ENUM (
    'SCHEDULED',
    'IN_PROGRESS',
    'COMPLETED',
    'MISSED',
    'CANCELLED'
);


ALTER TYPE public.callstatus OWNER TO pallcare;

--
-- Name: followuppriority; Type: TYPE; Schema: public; Owner: pallcare
--

CREATE TYPE public.followuppriority AS ENUM (
    'LOW',
    'MEDIUM',
    'HIGH',
    'URGENT'
);


ALTER TYPE public.followuppriority OWNER TO pallcare;

--
-- Name: gender; Type: TYPE; Schema: public; Owner: pallcare
--

CREATE TYPE public.gender AS ENUM (
    'MALE',
    'FEMALE',
    'OTHER',
    'UNKNOWN'
);


ALTER TYPE public.gender OWNER TO pallcare;

--
-- Name: medicationfrequency; Type: TYPE; Schema: public; Owner: pallcare
--

CREATE TYPE public.medicationfrequency AS ENUM (
    'ONCE_DAILY',
    'TWICE_DAILY',
    'THREE_TIMES_DAILY',
    'FOUR_TIMES_DAILY',
    'EVERY_MORNING',
    'EVERY_NIGHT',
    'EVERY_OTHER_DAY',
    'AS_NEEDED',
    'WEEKLY',
    'OTHER'
);


ALTER TYPE public.medicationfrequency OWNER TO pallcare;

--
-- Name: medicationroute; Type: TYPE; Schema: public; Owner: pallcare
--

CREATE TYPE public.medicationroute AS ENUM (
    'ORAL',
    'SUBLINGUAL',
    'TOPICAL',
    'TRANSDERMAL',
    'INHALATION',
    'RECTAL',
    'SUBCUTANEOUS',
    'INTRAMUSCULAR',
    'INTRAVENOUS',
    'OTHER'
);


ALTER TYPE public.medicationroute OWNER TO pallcare;

--
-- Name: protocoltype; Type: TYPE; Schema: public; Owner: pallcare
--

CREATE TYPE public.protocoltype AS ENUM (
    'CANCER',
    'HEART_FAILURE',
    'COPD',
    'GENERAL'
);


ALTER TYPE public.protocoltype OWNER TO pallcare;

--
-- Name: userrole; Type: TYPE; Schema: public; Owner: pallcare
--

CREATE TYPE public.userrole AS ENUM (
    'ADMIN',
    'NURSE',
    'PHYSICIAN',
    'CAREGIVER'
);


ALTER TYPE public.userrole OWNER TO pallcare;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: assessments; Type: TABLE; Schema: public; Owner: pallcare
--

CREATE TABLE public.assessments (
    id integer NOT NULL,
    patient_id integer NOT NULL,
    protocol_id integer NOT NULL,
    conducted_by_id integer NOT NULL,
    call_id integer,
    assessment_date timestamp without time zone NOT NULL,
    responses json NOT NULL,
    symptoms json NOT NULL,
    interventions json,
    notes text,
    follow_up_needed boolean,
    follow_up_date timestamp without time zone,
    follow_up_priority public.followuppriority,
    ai_guidance text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.assessments OWNER TO pallcare;

--
-- Name: assessments_id_seq; Type: SEQUENCE; Schema: public; Owner: pallcare
--

CREATE SEQUENCE public.assessments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.assessments_id_seq OWNER TO pallcare;

--
-- Name: assessments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pallcare
--

ALTER SEQUENCE public.assessments_id_seq OWNED BY public.assessments.id;


--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: pallcare
--

CREATE TABLE public.audit_logs (
    id integer NOT NULL,
    user_id integer,
    action character varying(50) NOT NULL,
    resource_type character varying(50) NOT NULL,
    resource_id integer,
    details json,
    ip_address character varying(50),
    user_agent character varying(255),
    "timestamp" timestamp without time zone NOT NULL
);


ALTER TABLE public.audit_logs OWNER TO pallcare;

--
-- Name: audit_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: pallcare
--

CREATE SEQUENCE public.audit_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.audit_logs_id_seq OWNER TO pallcare;

--
-- Name: audit_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pallcare
--

ALTER SEQUENCE public.audit_logs_id_seq OWNED BY public.audit_logs.id;


--
-- Name: calls; Type: TABLE; Schema: public; Owner: pallcare
--

CREATE TABLE public.calls (
    id integer NOT NULL,
    patient_id integer NOT NULL,
    conducted_by_id integer,
    scheduled_time timestamp without time zone NOT NULL,
    start_time timestamp without time zone,
    end_time timestamp without time zone,
    duration double precision,
    status public.callstatus NOT NULL,
    call_type character varying(50) NOT NULL,
    twilio_call_sid character varying(50),
    recording_url character varying(255),
    transcript text,
    notes text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.calls OWNER TO pallcare;

--
-- Name: calls_id_seq; Type: SEQUENCE; Schema: public; Owner: pallcare
--

CREATE SEQUENCE public.calls_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.calls_id_seq OWNER TO pallcare;

--
-- Name: calls_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pallcare
--

ALTER SEQUENCE public.calls_id_seq OWNED BY public.calls.id;


--
-- Name: medications; Type: TABLE; Schema: public; Owner: pallcare
--

CREATE TABLE public.medications (
    id integer NOT NULL,
    patient_id integer NOT NULL,
    name character varying(255) NOT NULL,
    dosage character varying(100) NOT NULL,
    dosage_unit character varying(50) NOT NULL,
    route public.medicationroute NOT NULL,
    frequency public.medicationfrequency NOT NULL,
    custom_frequency character varying(255),
    indication character varying(255),
    prescriber character varying(255),
    start_date date NOT NULL,
    end_date date,
    instructions text,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.medications OWNER TO pallcare;

--
-- Name: medications_id_seq; Type: SEQUENCE; Schema: public; Owner: pallcare
--

CREATE SEQUENCE public.medications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.medications_id_seq OWNER TO pallcare;

--
-- Name: medications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pallcare
--

ALTER SEQUENCE public.medications_id_seq OWNED BY public.medications.id;


--
-- Name: patients; Type: TABLE; Schema: public; Owner: pallcare
--

CREATE TABLE public.patients (
    id integer NOT NULL,
    mrn character varying(50) NOT NULL,
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    date_of_birth date NOT NULL,
    gender public.gender NOT NULL,
    phone_number character varying(20) NOT NULL,
    email character varying(120),
    address text,
    primary_diagnosis character varying(255) NOT NULL,
    secondary_diagnoses text,
    protocol_type public.protocoltype NOT NULL,
    primary_nurse_id integer NOT NULL,
    emergency_contact_name character varying(200),
    emergency_contact_phone character varying(20),
    emergency_contact_relationship character varying(50),
    advance_directive boolean,
    dnr_status boolean,
    allergies text,
    notes text,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.patients OWNER TO pallcare;

--
-- Name: patients_id_seq; Type: SEQUENCE; Schema: public; Owner: pallcare
--

CREATE SEQUENCE public.patients_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.patients_id_seq OWNER TO pallcare;

--
-- Name: patients_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pallcare
--

ALTER SEQUENCE public.patients_id_seq OWNED BY public.patients.id;


--
-- Name: protocols; Type: TABLE; Schema: public; Owner: pallcare
--

CREATE TABLE public.protocols (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    protocol_type public.protocoltype NOT NULL,
    version character varying(20) NOT NULL,
    questions json NOT NULL,
    decision_tree json NOT NULL,
    interventions json NOT NULL,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.protocols OWNER TO pallcare;

--
-- Name: protocols_id_seq; Type: SEQUENCE; Schema: public; Owner: pallcare
--

CREATE SEQUENCE public.protocols_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.protocols_id_seq OWNER TO pallcare;

--
-- Name: protocols_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pallcare
--

ALTER SEQUENCE public.protocols_id_seq OWNED BY public.protocols.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: pallcare
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(80) NOT NULL,
    email character varying(120) NOT NULL,
    password character varying(255) NOT NULL,
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    role public.userrole NOT NULL,
    phone_number character varying(20),
    license_number character varying(50),
    is_active boolean,
    login_attempts integer,
    last_login_at timestamp without time zone,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.users OWNER TO pallcare;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: pallcare
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO pallcare;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pallcare
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: assessments id; Type: DEFAULT; Schema: public; Owner: pallcare
--

ALTER TABLE ONLY public.assessments ALTER COLUMN id SET DEFAULT nextval('public.assessments_id_seq'::regclass);


--
-- Name: audit_logs id; Type: DEFAULT; Schema: public; Owner: pallcare
--

ALTER TABLE ONLY public.audit_logs ALTER COLUMN id SET DEFAULT nextval('public.audit_logs_id_seq'::regclass);


--
-- Name: calls id; Type: DEFAULT; Schema: public; Owner: pallcare
--

ALTER TABLE ONLY public.calls ALTER COLUMN id SET DEFAULT nextval('public.calls_id_seq'::regclass);


--
-- Name: medications id; Type: DEFAULT; Schema: public; Owner: pallcare
--

ALTER TABLE ONLY public.medications ALTER COLUMN id SET DEFAULT nextval('public.medications_id_seq'::regclass);


--
-- Name: patients id; Type: DEFAULT; Schema: public; Owner: pallcare
--

ALTER TABLE ONLY public.patients ALTER COLUMN id SET DEFAULT nextval('public.patients_id_seq'::regclass);


--
-- Name: protocols id; Type: DEFAULT; Schema: public; Owner: pallcare
--

ALTER TABLE ONLY public.protocols ALTER COLUMN id SET DEFAULT nextval('public.protocols_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: pallcare
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: assessments; Type: TABLE DATA; Schema: public; Owner: pallcare
--

COPY public.assessments (id, patient_id, protocol_id, conducted_by_id, call_id, assessment_date, responses, symptoms, interventions, notes, follow_up_needed, follow_up_date, follow_up_priority, ai_guidance, created_at, updated_at) FROM stdin;
130	20	2	27	\N	2025-03-25 14:30:00	{"dyspnea": {"value": 9}, "edema": {"value": 10}, "orthopnea": {"value": 6}, "fatigue": {"value": 8}, "chest_pain": {"value": true}}	{"dyspnea": 9, "edema": 10, "orthopnea": 6, "fatigue": 8, "chest_pain": 1}	[{"id": "severe_dyspnea", "title": "Severe Dyspnea Management", "description": "Urgent evaluation needed. Review diuretic regimen and consider supplemental oxygen."}, {"id": "severe_edema", "title": "Severe Edema Management", "description": "Review diuretic regimen. Consider temporary increase in diuretic dose."}, {"id": "chest_pain_management", "title": "Chest Pain Management", "description": "Evaluate for cardiac causes. Consider nitroglycerin if prescribed."}]	Follow-up check shows worsening symptoms. Patient sent to emergency department for evaluation.	t	2025-04-02 10:00:00	HIGH	Urgent hospital evaluation recommended. Possible acute decompensated heart failure with cardiac ischemia.	2025-04-02 18:38:56.131191	2025-04-02 18:58:38.640113
131	19	1	26	\N	2025-03-05 09:30:56.125266	{"pain_level": {"value": 4}, "pain_location": {"value": "Lower back"}, "nausea": {"value": 2}, "fatigue": {"value": 5}, "appetite": {"value": 6}}	{"pain": 4, "nausea": 2, "fatigue": 5, "appetite": 6}	[{"id": "moderate_pain", "title": "Moderate Pain Management", "description": "Review current analgesics. Consider scheduled dosing instead of as-needed."}]	Patient reports stable pain with current medication regimen	f	\N	\N	\N	2025-04-02 18:38:56.139199	2025-04-02 18:38:56.1392
132	19	1	26	\N	2025-03-08 14:00:56.125266	{"pain_level": {"value": 5}, "pain_location": {"value": "Lower back and right hip"}, "nausea": {"value": 3}, "fatigue": {"value": 6}, "appetite": {"value": 5}}	{"pain": 5, "nausea": 3, "fatigue": 6, "appetite": 5}	[{"id": "moderate_pain", "title": "Moderate Pain Management", "description": "Review current analgesics. Consider scheduled dosing instead of as-needed."}]	Patient reports slight increase in pain, spreading to hip	t	\N	LOW	\N	2025-04-02 18:38:56.139201	2025-04-02 18:38:56.139201
133	19	1	26	\N	2025-03-12 10:15:56.125266	{"pain_level": {"value": 6}, "pain_location": {"value": "Lower back and right hip"}, "nausea": {"value": 4}, "fatigue": {"value": 6}, "appetite": {"value": 4}}	{"pain": 6, "nausea": 4, "fatigue": 6, "appetite": 4}	[{"id": "moderate_pain", "title": "Moderate Pain Management", "description": "Review current analgesics. Consider scheduled dosing instead of as-needed."}]	Continued increase in pain. Referred to physician for medication adjustment	t	\N	MEDIUM	\N	2025-04-02 18:38:56.139201	2025-04-02 18:38:56.139201
134	19	1	26	\N	2025-03-15 11:00:56.125266	{"pain_level": {"value": 4}, "pain_location": {"value": "Lower back and right hip"}, "nausea": {"value": 5}, "fatigue": {"value": 5}, "appetite": {"value": 3}}	{"pain": 4, "nausea": 5, "fatigue": 5, "appetite": 3}	[{"id": "moderate_pain", "title": "Moderate Pain Management", "description": "Review current analgesics. Consider scheduled dosing instead of as-needed."}]	Pain improved after medication adjustment but nausea increased - likely side effect	t	\N	MEDIUM	\N	2025-04-02 18:38:56.139201	2025-04-02 18:38:56.139202
135	19	1	26	\N	2025-03-19 09:30:56.125266	{"pain_level": {"value": 3}, "pain_location": {"value": "Lower back and right hip"}, "nausea": {"value": 3}, "fatigue": {"value": 4}, "appetite": {"value": 4}}	{"pain": 3, "nausea": 3, "fatigue": 4, "appetite": 4}	[{"id": "mild_pain", "title": "Mild Pain Management", "description": "Continue current pain management. Monitor for changes."}]	Pain and nausea both improved. Anti-nausea medication effective	f	\N	\N	\N	2025-04-02 18:38:56.139202	2025-04-02 18:38:56.139202
136	19	1	26	\N	2025-03-22 14:00:56.125266	{"pain_level": {"value": 5}, "pain_location": {"value": "Lower back, right hip, and now radiating to leg"}, "nausea": {"value": 2}, "fatigue": {"value": 6}, "appetite": {"value": 4}}	{"pain": 5, "nausea": 2, "fatigue": 6, "appetite": 4}	[{"id": "moderate_pain", "title": "Moderate Pain Management", "description": "Review current analgesics. Consider scheduled dosing instead of as-needed."}]	New pain location reported - now radiating to leg. Discussed with physician	t	\N	MEDIUM	\N	2025-04-02 18:38:56.139202	2025-04-02 18:38:56.139202
137	19	1	26	\N	2025-03-26 10:15:56.125266	{"pain_level": {"value": 6}, "pain_location": {"value": "Lower back, right hip, and radiating to leg"}, "nausea": {"value": 2}, "fatigue": {"value": 7}, "appetite": {"value": 3}}	{"pain": 6, "nausea": 2, "fatigue": 7, "appetite": 3}	[{"id": "moderate_pain", "title": "Moderate Pain Management", "description": "Review current analgesics. Consider scheduled dosing instead of as-needed."}, {"id": "severe_fatigue", "title": "Severe Fatigue Management", "description": "Assess for reversible causes. Consider energy conservation strategies."}]	Increasing pain and fatigue. Scheduled for follow-up with oncologist	t	\N	HIGH	\N	2025-04-02 18:38:56.139203	2025-04-02 18:38:56.139203
138	19	1	26	\N	2025-03-30 11:00:56.125266	{"pain_level": {"value": 7}, "pain_location": {"value": "Lower back, right hip, and radiating to leg"}, "nausea": {"value": 3}, "fatigue": {"value": 7}, "appetite": {"value": 2}}	{"pain": 7, "nausea": 3, "fatigue": 7, "appetite": 2}	[{"id": "severe_pain", "title": "Severe Pain Management", "description": "Urgent review of pain medication. Consider opioid rotation or adjustment."}, {"id": "severe_fatigue", "title": "Severe Fatigue Management", "description": "Assess for reversible causes. Consider energy conservation strategies."}]	Pain continues to increase despite medication adjustments. Oncologist appointment scheduled for tomorrow	t	\N	HIGH	\N	2025-04-02 18:38:56.139203	2025-04-02 18:38:56.139203
127	19	1	26	25	2025-04-01 10:20:00	{"pain_level": {"value": 7}, "pain_location": {"value": "Lower back and hips"}, "nausea": {"value": 3}, "fatigue": {"value": 6}, "appetite": {"value": 4}}	{"pain": 7, "nausea": 3, "fatigue": 6, "appetite": 4}	[{"id": "severe_pain", "title": "Severe Pain Management", "description": "Urgent review of pain medication. Consider opioid rotation or adjustment."}]	Patient reports pain medication not lasting full duration between doses	t	2025-04-03 10:00:00	HIGH	Recommend increasing morphine dosage or frequency. Consider adding breakthrough pain medication.	2025-04-02 18:38:56.122032	2025-04-02 18:38:56.122033
128	20	2	27	26	2025-04-01 14:18:00	{"dyspnea": {"value": 5}, "edema": {"value": 7}, "orthopnea": {"value": 3}, "fatigue": {"value": 6}, "chest_pain": {"value": false}}	{"dyspnea": 5, "edema": 7, "orthopnea": 3, "fatigue": 6, "chest_pain": 0}	[{"id": "severe_edema", "title": "Severe Edema Management", "description": "Review diuretic regimen. Consider temporary increase in diuretic dose."}]	Patient has been compliant with fluid restriction but still has increased edema	t	2025-04-03 14:00:00	MEDIUM	Consider temporary increase in furosemide dose. Monitor weight daily and fluid intake.	2025-04-02 18:38:56.122034	2025-04-02 18:38:56.122034
129	20	2	27	\N	2025-03-25 09:30:00	{"dyspnea": {"value": 8}, "edema": {"value": 9}, "orthopnea": {"value": 5}, "fatigue": {"value": 7}, "chest_pain": {"value": true}}	{"dyspnea": 8, "edema": 9, "orthopnea": 5, "fatigue": 7, "chest_pain": 1}	[{"id": "severe_dyspnea", "title": "Severe Dyspnea Management", "description": "Urgent evaluation needed. Review diuretic regimen and consider supplemental oxygen."}, {"id": "severe_edema", "title": "Severe Edema Management", "description": "Review diuretic regimen. Consider temporary increase in diuretic dose."}, {"id": "chest_pain_management", "title": "Chest Pain Management", "description": "Evaluate for cardiac causes. Consider nitroglycerin if prescribed."}]	Patient reports severe increase in edema, dyspnea, and new onset chest pain. Needs immediate medical attention.	t	2025-04-02 10:00:00	HIGH	Urgent review by physician recommended. Consider hospital evaluation for decompensated heart failure with possible acute coronary syndrome. Increase diuretic dose and monitor fluid status closely.	2025-04-02 18:38:56.131189	2025-04-02 18:38:56.13119
139	20	2	27	\N	2025-03-05 10:00:56.125266	{"dyspnea": {"value": 3}, "edema": {"value": 4}, "orthopnea": {"value": 2}, "fatigue": {"value": 4}, "chest_pain": {"value": false}}	{"dyspnea": 3, "edema": 4, "orthopnea": 2, "fatigue": 4, "chest_pain": 0}	\N	Patient stable on current medication regimen	f	\N	\N	\N	2025-04-02 18:38:56.140773	2025-04-02 18:38:56.140775
140	20	2	27	\N	2025-03-12 14:30:56.125266	{"dyspnea": {"value": 4}, "edema": {"value": 5}, "orthopnea": {"value": 2}, "fatigue": {"value": 5}, "chest_pain": {"value": false}}	{"dyspnea": 4, "edema": 5, "orthopnea": 2, "fatigue": 5, "chest_pain": 0}	\N	Slight increase in edema and fatigue. Recommended fluid restriction	t	\N	LOW	\N	2025-04-02 18:38:56.140776	2025-04-02 18:38:56.140776
141	20	2	27	\N	2025-03-19 11:15:56.125266	{"dyspnea": {"value": 4}, "edema": {"value": 6}, "orthopnea": {"value": 3}, "fatigue": {"value": 5}, "chest_pain": {"value": false}}	{"dyspnea": 4, "edema": 6, "orthopnea": 3, "fatigue": 5, "chest_pain": 0}	\N	Edema increasing despite fluid restriction. Recommended diuretic adjustment	t	\N	MEDIUM	\N	2025-04-02 18:38:56.140776	2025-04-02 18:38:56.140776
142	20	2	27	\N	2025-03-26 09:45:56.125266	{"dyspnea": {"value": 5}, "edema": {"value": 7}, "orthopnea": {"value": 4}, "fatigue": {"value": 6}, "chest_pain": {"value": false}}	{"dyspnea": 5, "edema": 7, "orthopnea": 4, "fatigue": 6, "chest_pain": 0}	[{"id": "severe_edema", "title": "Severe Edema Management", "description": "Review diuretic regimen. Consider temporary increase in diuretic dose."}]	Significant increase in edema and now requiring more pillows to sleep. Diuretic dose increased	t	\N	HIGH	\N	2025-04-02 18:38:56.141963	2025-04-02 18:38:56.141964
143	20	2	27	\N	2025-03-29 10:30:56.125266	{"dyspnea": {"value": 4}, "edema": {"value": 5}, "orthopnea": {"value": 3}, "fatigue": {"value": 5}, "chest_pain": {"value": false}}	{"dyspnea": 4, "edema": 5, "orthopnea": 3, "fatigue": 5, "chest_pain": 0}	\N	Improvement in symptoms with increased diuretic dose	t	\N	MEDIUM	\N	2025-04-02 18:38:56.142449	2025-04-02 18:38:56.142449
144	21	3	26	\N	2025-03-12 11:30:56.125266	{"dyspnea": {"value": 5}, "cough": {"value": 4}, "sputum_color": {"value": "White"}, "oxygen_use": {"value": 16}, "anxiety": {"value": 4}}	{"dyspnea": 5, "cough": 4, "sputum": 2, "oxygen_use": 16, "anxiety": 4}	\N	Stable respiratory status. Using oxygen as prescribed	f	\N	\N	\N	2025-04-02 18:38:56.14245	2025-04-02 18:38:56.14245
145	21	3	26	\N	2025-03-19 14:15:56.125266	{"dyspnea": {"value": 6}, "cough": {"value": 5}, "sputum_color": {"value": "Yellow"}, "oxygen_use": {"value": 18}, "anxiety": {"value": 5}}	{"dyspnea": 6, "cough": 5, "sputum": 3, "oxygen_use": 18, "anxiety": 5}	\N	Increasing shortness of breath and cough. Sputum now yellow	t	\N	MEDIUM	\N	2025-04-02 18:38:56.14245	2025-04-02 18:38:56.14245
146	21	3	26	\N	2025-03-26 10:00:56.125266	{"dyspnea": {"value": 7}, "cough": {"value": 6}, "sputum_color": {"value": "Green"}, "oxygen_use": {"value": 21}, "anxiety": {"value": 7}}	{"dyspnea": 7, "cough": 6, "sputum": 4, "oxygen_use": 21, "anxiety": 7}	[{"id": "severe_dyspnea_copd", "title": "Severe Dyspnea Management for COPD", "description": "Review bronchodilator use. Consider rescue pack if available."}, {"id": "infection_evaluation", "title": "Respiratory Infection Evaluation", "description": "Evaluate for respiratory infection. Consider antibiotics per protocol."}, {"id": "severe_anxiety", "title": "Respiratory Anxiety Management", "description": "Review breathing techniques. Consider anxiolytic if severe."}]	Likely respiratory infection. Started on antibiotics and increased bronchodilator use	t	\N	HIGH	\N	2025-04-02 18:38:56.143029	2025-04-02 18:38:56.14303
147	21	3	26	\N	2025-03-30 11:45:56.125266	{"dyspnea": {"value": 5}, "cough": {"value": 5}, "sputum_color": {"value": "Yellow"}, "oxygen_use": {"value": 18}, "anxiety": {"value": 5}}	{"dyspnea": 5, "cough": 5, "sputum": 3, "oxygen_use": 18, "anxiety": 5}	\N	Improving with antibiotics. Breathing easier and sputum changing from green to yellow	t	\N	MEDIUM	\N	2025-04-02 18:38:56.143752	2025-04-02 18:38:56.143753
\.


--
-- Data for Name: audit_logs; Type: TABLE DATA; Schema: public; Owner: pallcare
--

COPY public.audit_logs (id, user_id, action, resource_type, resource_id, details, ip_address, user_agent, "timestamp") FROM stdin;
34	25	login	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0	2025-04-02 18:48:07.240498
35	25	login	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-02 19:08:18.971772
36	25	login	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0	2025-04-03 18:49:19.601666
37	25	view	call	28	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0	2025-04-03 18:50:38.486628
38	25	view	call	28	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0	2025-04-03 18:50:41.578101
39	25	view	call	28	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0	2025-04-03 18:50:41.587029
40	25	view	call	28	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0	2025-04-03 18:50:45.249443
41	25	login	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-03 22:10:34.72539
42	25	view	call	28	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-03 22:12:11.064721
43	25	view	call	28	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-03 22:12:11.082547
44	26	login	user	26	null	192.168.65.1	Python-urllib/3.8	2025-04-03 22:53:46.111445
45	25	login	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 02:44:56.677959
46	25	login	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 05:20:20.311012
47	25	view	call	28	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 05:20:58.149791
48	25	view	call	27	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 05:21:00.738126
49	25	view	call	26	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 05:21:03.347147
50	25	view	call	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 05:21:11.003592
51	25	view	call	27	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 05:21:18.083073
52	25	view	call	28	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 05:21:21.147361
53	25	view	call	28	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 05:21:26.948546
54	25	view	call	27	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 05:21:29.724047
55	25	view	call	26	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 05:21:32.073929
56	25	view	call	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 05:21:34.894599
57	25	view	call	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 05:21:37.118894
58	25	logout	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 05:23:37.589059
59	25	login	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 05:25:47.949887
60	25	view	call	28	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 05:26:47.256479
61	25	logout	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 05:41:34.496
62	25	login	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 05:41:41.353442
63	25	logout	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 05:44:29.872383
64	25	login	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 05:44:36.485314
65	25	login	user	25	null	172.18.0.3	python-requests/2.32.3	2025-04-04 05:49:09.732433
66	25	login	user	25	null	172.18.0.3	python-requests/2.32.3	2025-04-04 05:49:35.345981
67	26	login	user	26	null	172.18.0.3	python-requests/2.32.3	2025-04-04 05:49:41.929054
68	25	logout	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 05:49:54.771714
69	25	login	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 05:50:01.777387
70	25	login	user	25	null	172.18.0.3	python-requests/2.32.3	2025-04-04 05:56:16.938909
71	25	login	user	25	null	172.18.0.3	python-requests/2.32.3	2025-04-04 05:56:24.198099
72	25	login	user	25	null	172.18.0.3	python-requests/2.32.3	2025-04-04 05:56:35.80461
73	25	login	user	25	null	172.18.0.3	python-requests/2.32.3	2025-04-04 05:57:16.399283
74	25	login	user	25	null	172.18.0.3	python-requests/2.32.3	2025-04-04 05:57:24.127483
75	25	logout	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 05:58:11.479953
76	25	login	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 05:58:19.549375
77	25	logout	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 06:10:01.317973
78	25	login	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 06:10:08.699094
79	25	logout	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 06:36:25.486473
80	25	login	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 06:36:32.348863
81	25	view	call	28	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 06:37:06.153571
82	25	view	call	27	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 06:37:08.763064
83	25	view	call	26	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 06:37:11.244846
84	25	view	call	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 06:37:16.769003
85	25	view	call	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 06:37:19.954894
86	25	view	call	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 06:37:21.135091
87	25	login	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 07:09:02.323441
88	25	logout	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 07:09:44.530092
89	25	login	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 07:10:45.72633
90	25	logout	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 07:13:52.146249
91	25	login	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 07:14:35.464057
92	25	logout	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 07:18:55.779631
93	25	login	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 07:19:03.014547
94	25	login	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 19:54:12.794466
95	25	login	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-04 22:29:46.47346
96	25	login	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-05 04:09:13.691813
97	25	logout	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-05 04:12:46.395215
98	26	login	user	26	null	192.168.65.1	Python-urllib/3.8	2025-04-05 18:10:34.33532
99	26	login	user	26	null	192.168.65.1	Python-urllib/3.8	2025-04-05 18:10:34.544822
100	26	login	user	26	null	127.0.0.1	Python-urllib/3.10	2025-04-05 18:10:40.909228
101	25	login	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-05 18:41:38.82006
102	25	login	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-06 02:26:00.000557
103	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 02:32:55.653268
104	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 02:33:05.687422
105	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 02:33:05.698355
106	25	logout	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-06 02:33:44.153739
107	26	login	user	26	null	192.168.65.1	Python-urllib/3.8	2025-04-06 02:34:14.643478
108	26	login	user	26	null	192.168.65.1	Python-urllib/3.8	2025-04-06 02:34:14.653413
109	26	login	user	26	null	192.168.65.1	Python-urllib/3.8	2025-04-06 02:34:14.662242
110	26	login	user	26	null	192.168.65.1	Python-urllib/3.8	2025-04-06 02:34:22.984858
111	26	login	user	26	null	192.168.65.1	Python-urllib/3.8	2025-04-06 02:34:23.167608
112	26	login	user	26	null	192.168.65.1	Python-urllib/3.8	2025-04-06 02:34:29.510833
113	26	login	user	26	null	192.168.65.1	Python-urllib/3.8	2025-04-06 02:34:29.5256
114	26	login	user	26	null	192.168.65.1	Python-urllib/3.8	2025-04-06 02:34:29.537013
115	26	login	user	26	null	127.0.0.1	Python-urllib/3.10	2025-04-06 02:34:29.735117
116	26	login	user	26	null	192.168.65.1	Python-urllib/3.8	2025-04-06 03:11:36.238344
117	26	login	user	26	null	192.168.65.1	Python-urllib/3.8	2025-04-06 03:11:36.250749
118	26	login	user	26	null	192.168.65.1	Python-urllib/3.8	2025-04-06 03:11:36.259624
119	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 03:11:50.568014
120	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 03:11:50.579674
121	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 03:11:50.58816
122	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 03:12:01.398311
123	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 03:12:01.503555
124	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 03:12:07.759066
125	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 03:12:07.771505
126	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 03:12:07.782882
127	26	login	user	26	null	127.0.0.1	Python-urllib/3.10	2025-04-06 03:12:07.974683
128	25	login	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-06 03:12:41.026374
129	25	login	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-06 03:57:18.760807
130	25	logout	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-06 03:57:58.228559
131	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 03:58:09.943285
132	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 03:58:10.058448
133	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 03:58:16.278616
134	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 03:58:16.290903
135	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 03:58:16.302054
136	26	login	user	26	null	127.0.0.1	Python-urllib/3.10	2025-04-06 03:58:16.494262
137	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 03:58:54.937921
138	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 03:58:55.044225
140	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 03:59:01.322313
141	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 03:59:01.33619
144	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 04:00:18.937334
145	26	login	user	26	null	192.168.65.1	Python-urllib/3.8	2025-04-06 04:02:07.464637
146	26	login	user	26	null	192.168.65.1	Python-urllib/3.8	2025-04-06 04:02:13.577449
148	26	login	user	26	null	192.168.65.1	Python-urllib/3.8	2025-04-06 04:02:22.436903
152	26	login	user	26	null	192.168.65.1	Python-urllib/3.8	2025-04-06 04:02:28.688746
153	26	login	user	26	null	192.168.65.1	Python-urllib/3.8	2025-04-06 04:02:28.708556
154	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 04:03:15.289657
155	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 04:03:15.38596
156	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 04:03:21.486842
157	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 04:03:21.502517
161	26	login	user	26	null	127.0.0.1	Python-urllib/3.10	2025-04-06 04:03:21.820897
162	26	login	user	26	null	192.168.65.1	Python-urllib/3.8	2025-04-06 04:04:32.970467
165	25	login	user	25	null	192.168.65.1	Python-urllib/3.8	2025-04-06 04:04:33.007541
166	26	login	user	26	null	192.168.65.1	Python-urllib/3.8	2025-04-06 04:04:33.01991
167	28	login	user	28	null	192.168.65.1	Python-urllib/3.8	2025-04-06 04:04:33.030053
168	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 04:04:49.123909
139	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 03:59:01.309275
142	26	login	user	26	null	127.0.0.1	Python-urllib/3.10	2025-04-06 03:59:01.533914
143	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 04:00:06.065536
147	26	login	user	26	null	192.168.65.1	Python-urllib/3.8	2025-04-06 04:02:13.594766
149	26	login	user	26	null	192.168.65.1	Python-urllib/3.8	2025-04-06 04:02:22.449291
150	26	login	user	26	null	192.168.65.1	Python-urllib/3.8	2025-04-06 04:02:22.459821
151	26	login	user	26	null	192.168.65.1	Python-urllib/3.8	2025-04-06 04:02:22.588584
158	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 04:03:21.590704
159	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 04:03:21.600944
160	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 04:03:21.610586
163	26	login	user	26	null	192.168.65.1	Python-urllib/3.8	2025-04-06 04:04:32.985973
164	26	login	user	26	null	192.168.65.1	Python-urllib/3.8	2025-04-06 04:04:32.996147
169	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 04:04:55.216443
170	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 04:04:55.229547
171	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 04:05:27.726816
172	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 04:05:27.837983
173	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 04:05:33.937422
174	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 04:05:33.960001
175	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 04:05:34.049817
176	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 04:05:34.061382
177	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 04:05:34.071225
178	25	login	user	25	null	192.168.65.1	Python-urllib/3.12	2025-04-06 04:05:34.081215
179	26	login	user	26	null	192.168.65.1	Python-urllib/3.12	2025-04-06 04:05:34.092616
180	28	login	user	28	null	192.168.65.1	Python-urllib/3.12	2025-04-06 04:05:34.10399
181	26	login	user	26	null	127.0.0.1	Python-urllib/3.10	2025-04-06 04:06:04.138193
182	25	login	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-06 04:06:48.858001
183	25	logout	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36	2025-04-06 04:17:08.042583
184	25	login	user	25	null	192.168.65.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0	2025-04-16 01:58:53.804975
\.


--
-- Data for Name: calls; Type: TABLE DATA; Schema: public; Owner: pallcare
--

COPY public.calls (id, patient_id, conducted_by_id, scheduled_time, start_time, end_time, duration, status, call_type, twilio_call_sid, recording_url, transcript, notes, created_at, updated_at) FROM stdin;
25	19	26	2025-04-01 10:00:00	2025-04-01 10:05:00	2025-04-01 10:20:00	900	COMPLETED	assessment	CA123456789	https://example.com/recordings/call1.mp3	Nurse: How are you feeling today? Patient: My pain has been worse, about a 7 out of 10.	Patient reported increased pain levels	2025-04-02 18:38:56.107117	2025-04-02 18:38:56.107119
26	20	27	2025-04-01 14:00:00	2025-04-01 14:02:00	2025-04-01 14:18:00	960	COMPLETED	assessment	CA987654321	https://example.com/recordings/call2.mp3	Nurse: How is your breathing today? Patient: A bit harder than usual, and my ankles are more swollen.	Patient reports increased edema in ankles	2025-04-02 18:38:56.10712	2025-04-02 18:38:56.10712
27	21	26	2025-04-02 11:00:00	\N	\N	\N	SCHEDULED	assessment	\N	\N	\N	\N	2025-04-02 18:38:56.10712	2025-04-02 18:38:56.10712
28	19	26	2025-04-03 10:00:00	\N	\N	\N	SCHEDULED	follow_up	\N	\N	\N	\N	2025-04-02 18:38:56.10712	2025-04-02 18:38:56.107121
\.


--
-- Data for Name: medications; Type: TABLE DATA; Schema: public; Owner: pallcare
--

COPY public.medications (id, patient_id, name, dosage, dosage_unit, route, frequency, custom_frequency, indication, prescriber, start_date, end_date, instructions, is_active, created_at, updated_at) FROM stdin;
25	19	Morphine Sulfate	15	mg	ORAL	EVERY_MORNING	\N	Pain management	Dr. Williams	2025-03-03	\N	Take with food	t	2025-04-02 18:38:56.100649	2025-04-02 18:38:56.100651
26	19	Ondansetron	4	mg	ORAL	AS_NEEDED	\N	Nausea	Dr. Williams	2025-03-03	\N	Take as needed for nausea, up to 3 times daily	t	2025-04-02 18:38:56.100651	2025-04-02 18:38:56.100651
27	20	Furosemide	40	mg	ORAL	TWICE_DAILY	\N	Edema management	Dr. Smith	2025-02-01	\N	Take first dose in morning, second dose no later than 4pm	t	2025-04-02 18:38:56.100652	2025-04-02 18:38:56.100652
28	21	Tiotropium	18	mcg	INHALATION	ONCE_DAILY	\N	COPD management	Dr. Johnson	2025-01-02	\N	Use once daily with HandiHaler device	t	2025-04-02 18:38:56.100652	2025-04-02 18:38:56.100652
\.


--
-- Data for Name: patients; Type: TABLE DATA; Schema: public; Owner: pallcare
--

COPY public.patients (id, mrn, first_name, last_name, date_of_birth, gender, phone_number, email, address, primary_diagnosis, secondary_diagnoses, protocol_type, primary_nurse_id, emergency_contact_name, emergency_contact_phone, emergency_contact_relationship, advance_directive, dnr_status, allergies, notes, is_active, created_at, updated_at) FROM stdin;
19	MRN12345	John	Doe	1950-05-15	MALE	555-111-2222	john.doe@example.com	123 Main St, Anytown, USA	Stage IV Lung Cancer	COPD, Hypertension	CANCER	26	Jane Doe	555-222-3333	Spouse	t	t	Penicillin	Patient prefers morning calls	t	2025-04-02 18:38:56.094916	2025-04-02 18:38:56.094917
21	MRN24680	James	Wilson	1953-03-10	MALE	555-555-6666	james.wilson@example.com	789 Pine St, Elsewhere, USA	End-stage COPD, GOLD Stage IV	Cor Pulmonale, Osteoporosis	COPD	26	Sarah Wilson	555-666-7777	Daughter	t	t	None known	Uses oxygen 24/7, 2L via nasal cannula	t	2025-04-02 18:38:56.094918	2025-04-02 18:38:56.094918
20	MRN67890	Mary	Johnson	1945-09-20	FEMALE	555-333-4444	mary.johnson@example.com	456 Oak Ave, Somewhere, USA	Heart Failure NYHA Class IV	Diabetes, Chronic Kidney Disease	HEART_FAILURE	26	Robert Johnson	555-444-5555	Son	t	t	Sulfa drugs	Hard of hearing, speak clearly and loudly	t	2025-04-02 18:38:56.094918	2025-04-02 18:58:38.634586
\.


--
-- Data for Name: protocols; Type: TABLE DATA; Schema: public; Owner: pallcare
--

COPY public.protocols (id, name, description, protocol_type, version, questions, decision_tree, interventions, is_active, created_at, updated_at) FROM stdin;
1	Cancer Palliative Care Protocol	Protocol for managing symptoms in patients with advanced cancer	CANCER	1.0	[{"id": "pain_level", "text": "On a scale of 0 to 10, how would you rate your pain?", "type": "numeric", "required": true, "symptom_type": "pain", "min_value": 0, "max_value": 10}, {"id": "pain_location", "text": "Where is your pain located?", "type": "text", "required": true, "symptom_type": "pain"}, {"id": "nausea", "text": "On a scale of 0 to 10, how would you rate your nausea?", "type": "numeric", "required": true, "symptom_type": "nausea", "min_value": 0, "max_value": 10}, {"id": "fatigue", "text": "On a scale of 0 to 10, how would you rate your fatigue?", "type": "numeric", "required": true, "symptom_type": "fatigue", "min_value": 0, "max_value": 10}, {"id": "appetite", "text": "On a scale of 0 to 10, how would you rate your appetite?", "type": "numeric", "required": true, "symptom_type": "appetite", "min_value": 0, "max_value": 10}]	[{"id": "pain_assessment", "symptom_type": "pain", "condition": ">=7", "intervention_ids": ["severe_pain"]}, {"id": "pain_moderate", "symptom_type": "pain", "condition": ">=4", "intervention_ids": ["moderate_pain"]}, {"id": "pain_mild", "symptom_type": "pain", "condition": "<4", "intervention_ids": ["mild_pain"]}, {"id": "nausea_severe", "symptom_type": "nausea", "condition": ">=7", "intervention_ids": ["severe_nausea"]}, {"id": "fatigue_severe", "symptom_type": "fatigue", "condition": ">=7", "intervention_ids": ["severe_fatigue"]}]	[{"id": "severe_pain", "title": "Severe Pain Management", "description": "Urgent review of pain medication. Consider opioid rotation or adjustment.", "symptom_type": "pain", "severity_threshold": 7}, {"id": "moderate_pain", "title": "Moderate Pain Management", "description": "Review current analgesics. Consider scheduled dosing instead of as-needed.", "symptom_type": "pain", "severity_threshold": 4}, {"id": "mild_pain", "title": "Mild Pain Management", "description": "Continue current pain management. Monitor for changes.", "symptom_type": "pain", "severity_threshold": 0}, {"id": "severe_nausea", "title": "Severe Nausea Management", "description": "Review antiemetic regimen. Consider adding a different class of antiemetic.", "symptom_type": "nausea", "severity_threshold": 7}, {"id": "severe_fatigue", "title": "Severe Fatigue Management", "description": "Assess for reversible causes. Consider energy conservation strategies.", "symptom_type": "fatigue", "severity_threshold": 7}]	t	2025-04-01 01:39:25.236801	2025-04-01 01:39:25.236802
2	Heart Failure Palliative Care Protocol	Protocol for managing symptoms in patients with advanced heart failure	HEART_FAILURE	1.0	[{"id": "dyspnea", "text": "On a scale of 0 to 10, how would you rate your shortness of breath?", "type": "numeric", "required": true, "symptom_type": "dyspnea", "min_value": 0, "max_value": 10}, {"id": "edema", "text": "On a scale of 0 to 10, how would you rate the swelling in your legs or ankles?", "type": "numeric", "required": true, "symptom_type": "edema", "min_value": 0, "max_value": 10}, {"id": "orthopnea", "text": "How many pillows do you need to sleep comfortably without shortness of breath?", "type": "numeric", "required": true, "symptom_type": "orthopnea", "min_value": 0, "max_value": 10}, {"id": "fatigue", "text": "On a scale of 0 to 10, how would you rate your fatigue?", "type": "numeric", "required": true, "symptom_type": "fatigue", "min_value": 0, "max_value": 10}, {"id": "chest_pain", "text": "Have you experienced any chest pain?", "type": "boolean", "required": true, "symptom_type": "chest_pain"}]	[{"id": "dyspnea_severe", "symptom_type": "dyspnea", "condition": ">=7", "intervention_ids": ["severe_dyspnea"]}, {"id": "edema_severe", "symptom_type": "edema", "condition": ">=7", "intervention_ids": ["severe_edema"]}, {"id": "chest_pain_present", "symptom_type": "chest_pain", "condition": "==true", "intervention_ids": ["chest_pain_management"]}]	[{"id": "severe_dyspnea", "title": "Severe Dyspnea Management", "description": "Urgent evaluation needed. Review diuretic regimen and consider supplemental oxygen.", "symptom_type": "dyspnea", "severity_threshold": 7}, {"id": "severe_edema", "title": "Severe Edema Management", "description": "Review diuretic regimen. Consider temporary increase in diuretic dose.", "symptom_type": "edema", "severity_threshold": 7}, {"id": "chest_pain_management", "title": "Chest Pain Management", "description": "Evaluate for cardiac causes. Consider nitroglycerin if prescribed.", "symptom_type": "chest_pain"}]	t	2025-04-01 01:39:25.236803	2025-04-01 01:39:25.236803
3	COPD Palliative Care Protocol	Protocol for managing symptoms in patients with advanced COPD	COPD	1.0	[{"id": "dyspnea", "text": "On a scale of 0 to 10, how would you rate your shortness of breath?", "type": "numeric", "required": true, "symptom_type": "dyspnea", "min_value": 0, "max_value": 10}, {"id": "cough", "text": "On a scale of 0 to 10, how would you rate your cough?", "type": "numeric", "required": true, "symptom_type": "cough", "min_value": 0, "max_value": 10}, {"id": "sputum_color", "text": "What color is your sputum/phlegm?", "type": "choice", "required": true, "symptom_type": "sputum", "choices": ["Clear", "White", "Yellow", "Green"]}, {"id": "oxygen_use", "text": "How many hours per day are you using oxygen?", "type": "numeric", "required": true, "symptom_type": "oxygen_use", "min_value": 0, "max_value": 24}, {"id": "anxiety", "text": "On a scale of 0 to 10, how would you rate your anxiety related to breathing?", "type": "numeric", "required": true, "symptom_type": "anxiety", "min_value": 0, "max_value": 10}]	[{"id": "dyspnea_severe", "symptom_type": "dyspnea", "condition": ">=7", "intervention_ids": ["severe_dyspnea_copd"]}, {"id": "sputum_green", "symptom_type": "sputum", "condition": "==Green", "intervention_ids": ["infection_evaluation"]}, {"id": "anxiety_severe", "symptom_type": "anxiety", "condition": ">=7", "intervention_ids": ["severe_anxiety"]}]	[{"id": "severe_dyspnea_copd", "title": "Severe Dyspnea Management for COPD", "description": "Review bronchodilator use. Consider rescue pack if available.", "symptom_type": "dyspnea", "severity_threshold": 7}, {"id": "infection_evaluation", "title": "Respiratory Infection Evaluation", "description": "Evaluate for respiratory infection. Consider antibiotics per protocol.", "symptom_type": "sputum"}, {"id": "severe_anxiety", "title": "Respiratory Anxiety Management", "description": "Review breathing techniques. Consider anxiolytic if severe.", "symptom_type": "anxiety", "severity_threshold": 7}]	t	2025-04-01 01:39:25.236803	2025-04-01 01:39:25.236803
4	Cancer Palliative Care Protocol	Assessment and management protocol for patients with advanced cancer, focusing on pain, nausea, fatigue, and emotional symptoms.	CANCER	1.0.0	[{"id": "pain_location", "text": "Are you currently experiencing any pain? If so, where is the pain located?", "type": "text", "required": true, "symptom_type": "pain", "category": "Physical Symptoms"}, {"id": "pain_severity", "text": "On a scale of 0 to 10, with 0 being no pain and 10 being the worst possible pain, how would you rate your current level of pain?", "type": "numeric", "required": true, "symptom_type": "pain", "min_value": 0, "max_value": 10, "category": "Physical Symptoms"}, {"id": "pain_quality", "text": "How would you describe the quality or type of pain you are experiencing (e.g., dull, sharp, burning, etc.)?", "type": "text", "required": true, "symptom_type": "pain", "category": "Physical Symptoms"}, {"id": "pain_relief", "text": "What measures have you tried to relieve your pain (e.g., medication, hot/cold packs, positioning, etc.), and how effective have they been?", "type": "text", "required": true, "symptom_type": "pain", "category": "Physical Symptoms"}, {"id": "nausea_vomiting", "text": "Have you experienced any nausea or vomiting in the past 24 hours?", "type": "boolean", "required": true, "symptom_type": "nausea_vomiting", "category": "Physical Symptoms"}, {"id": "nausea_vomiting_severity", "text": "If you have experienced nausea or vomiting, on a scale of 0 to 10, with 0 being no nausea/vomiting and 10 being the worst possible, how would you rate the severity?", "type": "numeric", "required": false, "symptom_type": "nausea_vomiting", "min_value": 0, "max_value": 10, "category": "Physical Symptoms"}, {"id": "bowel_function", "text": "Have you experienced any constipation or changes in your bowel function in the past few days?", "type": "boolean", "required": true, "symptom_type": "constipation", "category": "Physical Symptoms"}, {"id": "bowel_function_details", "text": "If you have experienced constipation or changes in bowel function, please describe your symptoms (e.g., no bowel movement in X days, straining, hard stools, etc.).", "type": "text", "required": false, "symptom_type": "constipation", "category": "Physical Symptoms"}, {"id": "fatigue_level", "text": "On a scale of 0 to 10, with 0 being no fatigue and 10 being the worst possible fatigue, how would you rate your current level of fatigue or lack of energy?", "type": "numeric", "required": true, "symptom_type": "fatigue", "min_value": 0, "max_value": 10, "category": "Physical Symptoms"}, {"id": "appetite_changes", "text": "Have you experienced any changes in your appetite or weight in the past few weeks?", "type": "boolean", "required": true, "symptom_type": "appetite", "category": "Physical Symptoms"}, {"id": "appetite_changes_details", "text": "If you have experienced changes in appetite or weight, please describe the changes (e.g., decreased appetite, weight loss/gain, difficulty eating, etc.).", "type": "text", "required": false, "symptom_type": "appetite", "category": "Physical Symptoms"}, {"id": "anxiety_level", "text": "On a scale of 0 to 10, with 0 being no anxiety and 10 being the worst possible anxiety, how would you rate your current level of anxiety or worry?", "type": "numeric", "required": true, "symptom_type": "anxiety", "min_value": 0, "max_value": 10, "category": "Psychological Symptoms"}, {"id": "depression_level", "text": "On a scale of 0 to 10, with 0 being no depression and 10 being the worst possible depression, how would you rate your current level of sadness or depression?", "type": "numeric", "required": true, "symptom_type": "depression", "min_value": 0, "max_value": 10, "category": "Psychological Symptoms"}, {"id": "medication_side_effects", "text": "Have you experienced any side effects or problems with your current medications?", "type": "boolean", "required": true, "symptom_type": "medication_side_effects", "category": "Medication Management"}, {"id": "medication_side_effects_details", "text": "If you have experienced side effects or problems with your medications, please describe them (e.g., nausea, constipation, drowsiness, etc.).", "type": "text", "required": false, "symptom_type": "medication_side_effects", "category": "Medication Management"}, {"id": "caregiver_support", "text": "Do you have a caregiver or support system helping you at home?", "type": "boolean", "required": true, "symptom_type": "caregiver_support", "category": "Support System"}, {"id": "caregiver_burden", "text": "If you have a caregiver, on a scale of 0 to 10, with 0 being no burden and 10 being an extremely high burden, how would you rate the level of burden or stress on your caregiver?", "type": "numeric", "required": false, "symptom_type": "caregiver_burden", "min_value": 0, "max_value": 10, "category": "Support System"}]	[{"id": "node_pain_severe", "symptom_type": "pain", "condition": ">=", "value": 9, "next_node_id": null, "intervention_ids": ["uncontrolled_pain_emergency"]}, {"id": "node_pain_moderate", "symptom_type": "pain", "condition": ">=", "value": 6, "next_node_id": "node_breakthrough_pain", "intervention_ids": []}, {"id": "node_breakthrough_pain", "symptom_type": "pain", "condition": "==", "value": "neuropathic", "next_node_id": "node_neuropathic_pain", "intervention_ids": ["breakthrough_pain_intervention"]}, {"id": "node_neuropathic_pain", "symptom_type": "pain", "condition": ">=", "value": 4, "next_node_id": null, "intervention_ids": ["neuropathic_pain_intervention", "persistent_pain_intervention"]}, {"id": "node_pain_mild", "symptom_type": "pain", "condition": ">=", "value": 4, "next_node_id": null, "intervention_ids": ["persistent_pain_intervention"]}, {"id": "node_nausea_vomiting_severe", "symptom_type": "nausea_vomiting", "condition": ">=", "value": 7, "next_node_id": null, "intervention_ids": ["nausea_vomiting_intervention"]}, {"id": "node_nausea_vomiting_moderate", "symptom_type": "nausea_vomiting", "condition": ">=", "value": 4, "next_node_id": null, "intervention_ids": ["nausea_vomiting_intervention"]}, {"id": "node_constipation", "symptom_type": "constipation", "condition": "==", "value": true, "next_node_id": "node_constipation_severity", "intervention_ids": ["constipation_prevention"]}, {"id": "node_constipation_severity", "symptom_type": "constipation", "condition": ">=", "value": 4, "next_node_id": null, "intervention_ids": ["constipation_management"]}, {"id": "node_fatigue_severe", "symptom_type": "fatigue", "condition": ">=", "value": 8, "next_node_id": null, "intervention_ids": ["fatigue_management"]}, {"id": "node_fatigue_moderate", "symptom_type": "fatigue", "condition": ">=", "value": 5, "next_node_id": null, "intervention_ids": ["fatigue_management"]}, {"id": "node_anxiety_severe", "symptom_type": "anxiety", "condition": ">=", "value": 8, "next_node_id": null, "intervention_ids": ["anxiety_support"]}, {"id": "node_anxiety_moderate", "symptom_type": "anxiety", "condition": ">=", "value": 5, "next_node_id": null, "intervention_ids": ["anxiety_support"]}, {"id": "node_depression_severe", "symptom_type": "depression", "condition": ">=", "value": 8, "next_node_id": null, "intervention_ids": ["depression_support"]}, {"id": "node_depression_moderate", "symptom_type": "depression", "condition": ">=", "value": 5, "next_node_id": null, "intervention_ids": ["depression_support"]}, {"id": "node_medication_side_effects", "symptom_type": "medication_side_effects", "condition": "==", "value": true, "next_node_id": null, "intervention_ids": ["medication_side_effects"]}, {"id": "node_caregiver_burden_high", "symptom_type": "caregiver_burden", "condition": ">=", "value": 7, "next_node_id": null, "intervention_ids": ["caregiver_education"]}, {"id": "node_bowel_obstruction", "symptom_type": "bowel_obstruction", "condition": ">=", "value": 7, "next_node_id": null, "intervention_ids": ["malignant_bowel_obstruction"]}, {"id": "node_respiratory_distress", "symptom_type": "dyspnea", "condition": ">=", "value": 8, "next_node_id": null, "intervention_ids": ["respiratory_distress_emergency"]}]	[{"id": "persistent_pain_intervention", "title": "Persistent Pain Management", "description": "Adjust long-acting opioid medication dosage and schedule based on numeric pain rating scale and pain patterns over the past 24 hours.", "symptom_type": "pain", "severity_threshold": 4, "priority": "high", "instructions": "Take your long-acting opioid medication consistently as prescribed. Call the palliative care team if your average pain rating is 4 or higher over the past 24 hours to have your dosage adjusted."}, {"id": "breakthrough_pain_intervention", "title": "Breakthrough Pain Management", "description": "Use short-acting opioid medications as needed for temporary flare-ups or increases in pain intensity.", "symptom_type": "pain", "severity_threshold": 6, "priority": "medium", "instructions": "Take the prescribed breakthrough dose of short-acting opioid medication when your pain rating is 6 or higher. Wait 30-60 minutes and take another dose if pain persists."}, {"id": "neuropathic_pain_intervention", "title": "Neuropathic Pain Management", "description": "Add an adjuvant medication like gabapentin or a tricyclic antidepressant to help relieve neuropathic pain symptoms.", "symptom_type": "pain", "severity_threshold": 4, "priority": "medium", "instructions": "Take the prescribed adjuvant medication consistently to help relieve symptoms of burning, tingling or shooting neuropathic pain."}, {"id": "nausea_vomiting_intervention", "title": "Nausea and Vomiting Control", "description": "Prescribe anti-nausea medications based on characteristics and patterns of nausea and vomiting. May combine different anti-emetic classes.", "symptom_type": "nausea", "severity_threshold": 4, "priority": "high", "instructions": "Take the prescribed anti-nausea medication(s) consistently as directed. Call if you are unable to keep any foods or liquids down for more than 24 hours."}, {"id": "constipation_prevention", "title": "Constipation Prevention", "description": "Initiate a stimulant laxative and stool softener regimen to prevent constipation from developing with opioid use.", "symptom_type": "constipation", "severity_threshold": 0, "priority": "medium", "instructions": "Take the prescribed laxative and stool softener medications consistently to prevent constipation."}, {"id": "constipation_management", "title": "Constipation Management", "description": "For constipation not relieved by preventative regimen, use escalating interventions including osmotic laxatives, enemas, and manual disimpaction.", "symptom_type": "constipation", "severity_threshold": 4, "priority": "high", "instructions": "Call the palliative care team if you have not had a bowel movement in 3 or more days despite using laxatives. We may need to try additional treatments."}, {"id": "fatigue_management", "title": "Fatigue Management and Energy Conservation", "description": "Provide education on energy conservation techniques and schedule periods of rest. Consider medical treatments like steroids or psychostimulants.", "symptom_type": "fatigue", "severity_threshold": 5, "priority": "medium", "instructions": "Plan your daily routine to prioritize important activities. Build in rest periods before and after effortful tasks. Call if fatigue is severely impacting your ability to complete basic daily activities."}, {"id": "anxiety_support", "title": "Anxiety Support", "description": "Provide counseling, relaxation techniques, and consider anti-anxiety medications on a scheduled or as-needed basis.", "symptom_type": "anxiety", "severity_threshold": 5, "priority": "medium", "instructions": "Try relaxation and mindfulness exercises daily. Take the prescribed anti-anxiety medication if your anxiety is interfering significantly with your ability to function."}, {"id": "depression_support", "title": "Depression Support", "description": "Initiate counseling and prescribe an antidepressant medication to relieve symptoms of depression.", "symptom_type": "depression", "severity_threshold": 5, "priority": "high", "instructions": "Engage with the counseling resources provided. Take the prescribed antidepressant medication consistently as directed by your palliative care provider."}, {"id": "medication_side_effects", "title": "Medication Side Effect Management", "description": "Identify and treat common side effects like constipation, nausea, drowsiness from palliative medications through preventative regimens or adjuvant medications.", "symptom_type": "side effects", "severity_threshold": 4, "priority": "medium", "instructions": "Call the palliative team to report any new or worsening side effects from medications so we can adjust regimens or add medications to counteract the side effects."}, {"id": "caregiver_education", "title": "Caregiver Support and Education", "description": "Provide training to informal caregivers on care tasks, symptom identification, medication administration, and self-care.", "symptom_type": "caregiver support", "severity_threshold": 0, "priority": "medium", "instructions": "Engage with the educational resources and trainings provided to support you in your caregiver role. Don't hesitate to call with any questions or concerns."}, {"id": "respiratory_distress_emergency", "title": "Respiratory Distress Emergency Management", "description": "For acute respiratory distress or air hunger not relieved by supplemental oxygen, provide anxiolytic and opioid medications via appropriate routes.", "symptom_type": "dyspnea", "severity_threshold": 8, "priority": "urgent", "instructions": "Call emergency services immediately if experiencing severe shortness of breath or air hunger that is not relieved by supplemental oxygen after taking breakthrough medication."}, {"id": "uncontrolled_pain_emergency", "title": "Uncontrolled Pain Emergency Management", "description": "For episodes of severe, uncontrolled pain, provide breakthrough opioid doses via injectable or other rapid routes.", "symptom_type": "pain", "severity_threshold": 9, "priority": "urgent", "instructions": "Call emergency services or go to the emergency room if you are experiencing severe, unrelenting pain that is not relieved by your breakthrough medication regimen."}, {"id": "malignant_bowel_obstruction", "title": "Malignant Bowel Obstruction Management", "description": "For inpatient management of malignant bowel obstructions, decompress bowel, provide anti-emetics, analgesics, and consider surgery or venting gastrostomy.", "symptom_type": "bowel obstruction", "severity_threshold": 7, "priority": "high", "instructions": "Call the palliative care team or seek emergency care promptly if you develop worsening abdominal pain, nausea, vomiting and inability to have bowel movements which may indicate a bowel obstruction."}]	t	2025-04-01 01:41:23.529474	2025-04-01 01:41:23.529479
5	Heart Failure Protocol	Protocol for managing patients with advanced heart failure, addressing dyspnea, edema, activity tolerance, and medication adherence.	HEART_FAILURE	1.0.0	[{"id": "breathlessness_rest", "text": "On a scale of 0 to 10, with 0 being no breathlessness and 10 being the worst breathlessness imaginable, how would you rate your breathlessness while resting?", "type": "numeric", "required": true, "symptom_type": "dyspnea", "min_value": 0, "max_value": 10, "category": "Respiratory Symptoms"}, {"id": "breathlessness_activity", "text": "On the same 0 to 10 scale, how would you rate your breathlessness with typical daily activities?", "type": "numeric", "required": true, "symptom_type": "dyspnea", "min_value": 0, "max_value": 10, "category": "Respiratory Symptoms"}, {"id": "edema_location", "text": "Are you experiencing any swelling or puffiness in your legs, ankles, or abdomen?", "type": "boolean", "required": true, "symptom_type": "edema", "category": "Fluid Status"}, {"id": "edema_severity", "text": "On a scale of 0 to 10, with 0 being no swelling and 10 being severe swelling, how would you rate the extent of the swelling?", "type": "numeric", "required": false, "symptom_type": "edema", "min_value": 0, "max_value": 10, "category": "Fluid Status"}, {"id": "edema_changes", "text": "Has the swelling gotten worse, better, or stayed about the same over the past few days?", "type": "choice", "required": false, "symptom_type": "edema", "choices": ["Worse", "Better", "About the same"], "category": "Fluid Status"}, {"id": "chest_pain", "text": "Are you experiencing any chest pain, chest tightness, or chest discomfort?", "type": "boolean", "required": true, "symptom_type": "chest pain", "category": "Cardiac Symptoms"}, {"id": "chest_pain_severity", "text": "On a 0 to 10 scale, with 0 being no pain and 10 being the worst pain imaginable, how would you rate your chest pain or discomfort?", "type": "numeric", "required": false, "symptom_type": "chest pain", "min_value": 0, "max_value": 10, "category": "Cardiac Symptoms"}, {"id": "fatigue_level", "text": "On a scale of 0 to 10, with 0 being no fatigue and 10 being completely exhausted, how would you rate your overall fatigue level?", "type": "numeric", "required": true, "symptom_type": "fatigue", "min_value": 0, "max_value": 10, "category": "General Symptoms"}, {"id": "activity_tolerance", "text": "How does your current fatigue level impact your ability to complete typical daily activities?", "type": "text", "required": true, "symptom_type": "fatigue", "category": "General Symptoms"}, {"id": "sleep_quality", "text": "On a scale of 0 to 10, with 0 being no difficulties and 10 being severe difficulties, how would you rate the quality of your sleep over the past few nights?", "type": "numeric", "required": true, "symptom_type": "sleep", "min_value": 0, "max_value": 10, "category": "General Symptoms"}, {"id": "sleep_positioning", "text": "Do you need to sleep sitting upright or use multiple pillows to help with breathing at night?", "type": "boolean", "required": true, "symptom_type": "sleep", "category": "General Symptoms"}, {"id": "medication_adherence", "text": "Have you missed any doses of your heart failure medications in the past few days?", "type": "boolean", "required": true, "symptom_type": "medications", "category": "Medications"}, {"id": "medication_side_effects", "text": "Are you experiencing any bothersome side effects from your current medications?", "type": "boolean", "required": true, "symptom_type": "medications", "category": "Medications"}, {"id": "medication_side_effect_details", "text": "If yes, please describe the side effects you are experiencing.", "type": "text", "required": false, "symptom_type": "medications", "category": "Medications"}, {"id": "weight_changes", "text": "Have you noticed any significant changes in your weight over the past week or two?", "type": "boolean", "required": true, "symptom_type": "fluid status", "category": "Fluid Status"}, {"id": "appetite", "text": "How would you describe your appetite over the past few days?", "type": "choice", "required": true, "symptom_type": "nutrition", "choices": ["Poor", "Fair", "Good", "Excellent"], "category": "Nutrition"}, {"id": "diet_adherence", "text": "Have you been able to follow the recommended diet for heart failure patients?", "type": "boolean", "required": true, "symptom_type": "nutrition", "category": "Nutrition"}, {"id": "psychological_wellbeing", "text": "On a scale of 0 to 10, with 0 being the worst and 10 being the best, how would you rate your overall psychological and emotional wellbeing?", "type": "numeric", "required": true, "symptom_type": "psychological", "min_value": 0, "max_value": 10, "category": "Psychological Symptoms"}]	[{"id": "node_breathlessness_rest", "symptom_type": "dyspnea", "condition": ">=", "value": 7, "next_node_id": "node_emergency_breathlessness", "intervention_ids": []}, {"id": "node_emergency_breathlessness", "symptom_type": "dyspnea", "condition": null, "value": null, "next_node_id": null, "intervention_ids": ["emergency_breathlessness"]}, {"id": "node_breathlessness_rest", "symptom_type": "dyspnea", "condition": ">=", "value": 5, "next_node_id": "node_medication_breathlessness", "intervention_ids": ["oxygen_breathlessness"]}, {"id": "node_medication_breathlessness", "symptom_type": "dyspnea", "condition": null, "value": null, "next_node_id": null, "intervention_ids": ["medication_breathlessness"]}, {"id": "node_breathlessness_rest", "symptom_type": "dyspnea", "condition": ">=", "value": 3, "next_node_id": "node_positioning_breathlessness", "intervention_ids": []}, {"id": "node_positioning_breathlessness", "symptom_type": "dyspnea", "condition": null, "value": null, "next_node_id": null, "intervention_ids": ["positioning_breathlessness"]}, {"id": "node_edema_location", "symptom_type": "edema", "condition": "==", "value": true, "next_node_id": "node_edema_severity", "intervention_ids": []}, {"id": "node_edema_severity", "symptom_type": "edema", "condition": ">=", "value": 7, "next_node_id": "node_emergency_edema", "intervention_ids": []}, {"id": "node_emergency_edema", "symptom_type": "edema", "condition": null, "value": null, "next_node_id": null, "intervention_ids": ["emergency_edema"]}, {"id": "node_edema_severity", "symptom_type": "edema", "condition": ">=", "value": 5, "next_node_id": "node_diuretic_adjustment", "intervention_ids": ["edema_compression"]}, {"id": "node_diuretic_adjustment", "symptom_type": "edema", "condition": null, "value": null, "next_node_id": null, "intervention_ids": ["diuretic_adjustment"]}, {"id": "node_edema_severity", "symptom_type": "edema", "condition": ">=", "value": 3, "next_node_id": null, "intervention_ids": ["edema_elevation"]}, {"id": "node_chest_pain", "symptom_type": "chest pain", "condition": "==", "value": true, "next_node_id": "node_chest_pain_severity", "intervention_ids": []}, {"id": "node_chest_pain_severity", "symptom_type": "chest pain", "condition": ">=", "value": 5, "next_node_id": null, "intervention_ids": ["emergency_breathlessness"]}, {"id": "node_fatigue_level", "symptom_type": "fatigue", "condition": ">=", "value": 5, "next_node_id": "node_activity_recommendations", "intervention_ids": []}, {"id": "node_activity_recommendations", "symptom_type": "general", "condition": null, "value": null, "next_node_id": null, "intervention_ids": ["activity_recommendations"]}, {"id": "node_sleep_quality", "symptom_type": "sleep", "condition": ">=", "value": 5, "next_node_id": "node_sleep_positioning", "intervention_ids": []}, {"id": "node_sleep_positioning", "symptom_type": "general", "condition": null, "value": null, "next_node_id": null, "intervention_ids": ["sleep_positioning"]}, {"id": "node_medication_adherence", "symptom_type": "medications", "condition": "==", "value": true, "next_node_id": null, "intervention_ids": ["medication_adherence"]}, {"id": "node_psychological_wellbeing", "symptom_type": "psychological", "condition": "<=", "value": 5, "next_node_id": null, "intervention_ids": ["psychological_support", "activity_recommendations"]}, {"id": "node_diet_assessment", "symptom_type": "nutrition", "condition": null, "value": null, "next_node_id": null, "intervention_ids": ["diet_fluid_management"]}]	[{"id": "positioning_breathlessness", "title": "Positioning for Breathlessness Relief", "description": "Using proper positioning techniques can help alleviate breathlessness and improve respiratory mechanics in advanced heart failure.", "symptom_type": "dyspnea", "severity_threshold": 3, "priority": "medium", "instructions": "Sit upright or lean forward with arms resting on a table. This opens up the chest and allows for easier breathing. Use pillows to support your back and arms as needed."}, {"id": "oxygen_breathlessness", "title": "Supplemental Oxygen", "description": "Providing supplemental oxygen can improve oxygenation and relieve breathlessness in advanced heart failure when other measures are insufficient.", "symptom_type": "dyspnea", "severity_threshold": 4, "priority": "high", "instructions": "Use supplemental oxygen via nasal cannula or mask as prescribed by your physician. Start at 2-3 liters per minute and increase flow rate as needed to relieve shortness of breath."}, {"id": "medication_breathlessness", "title": "Medications for Breathlessness", "description": "Certain medications can be used to provide relief from breathlessness in advanced heart failure when non-pharmacologic measures are inadequate.", "symptom_type": "dyspnea", "severity_threshold": 5, "priority": "high", "instructions": "Take opioid medication (morphine or similar) as prescribed for severe breathlessness not relieved by other measures. Start with low doses and increase gradually as needed and tolerated."}, {"id": "edema_elevation", "title": "Elevation for Edema Management", "description": "Elevating the affected limb(s) above the level of the heart can help reduce swelling and edema caused by fluid accumulation in heart failure.", "symptom_type": "edema", "severity_threshold": 3, "priority": "medium", "instructions": "When sitting or resting, elevate your legs above the level of your heart using pillows or an ottoman. Try to keep legs elevated as much as possible during waking hours."}, {"id": "edema_compression", "title": "Compression for Edema Management", "description": "Properly fitted compression stockings can help reduce swelling and discomfort from edema in the legs and ankles caused by heart failure.", "symptom_type": "edema", "severity_threshold": 4, "priority": "high", "instructions": "Wear knee-high or thigh-high compression stockings daily as recommended by your care team. Put them on first thing in the morning before swelling worsens."}, {"id": "diuretic_adjustment", "title": "Adjusting Diuretic Medications", "description": "Changes in diuretic dosing may be needed to better manage fluid buildup and edema in advanced heart failure.", "symptom_type": "edema", "severity_threshold": 5, "priority": "high", "instructions": "If edema worsens despite other measures, contact your clinician about adjusting your diuretic (water pill) dose temporarily to help remove excess fluid."}, {"id": "activity_recommendations", "title": "Activity Recommendations", "description": "Recommending an appropriate level of daily activity and exercise can help manage heart failure symptoms.", "symptom_type": "general", "severity_threshold": 2, "priority": "medium", "instructions": "Engage in light activity like walking as tolerated, but avoid strenuous exertion. Break up activities into smaller portions and rest frequently as needed."}, {"id": "diet_fluid_management", "title": "Dietary and Fluid Management", "description": "Restricting salt, fluid, and certain nutrients in the diet can help control fluid buildup and related symptoms in heart failure.", "symptom_type": "general", "severity_threshold": 3, "priority": "high", "instructions": "Follow a low-sodium diet and restrict daily fluid intake to 1.5-2 liters or as recommended. Avoid foods high in potassium if kidney function is impaired."}, {"id": "sleep_positioning", "title": "Sleep Positioning", "description": "Adjusting sleep positioning can improve breathing and sleep quality for those with severe heart failure.", "symptom_type": "general", "severity_threshold": 4, "priority": "medium", "instructions": "Sleep with your head and upper body elevated using multiple pillows or a wedge. This can relieve breathlessness and edema at night."}, {"id": "psychological_support", "title": "Psychological and Emotional Support", "description": "Heart failure can take a significant emotional toll. Psychological support is an important part of palliative care.", "symptom_type": "psychosocial", "severity_threshold": 3, "priority": "high", "instructions": "Speak to a counselor or join a support group to discuss your emotions, fears, and coping strategies related to living with advanced heart failure."}, {"id": "medication_adherence", "title": "Medication Adherence Support", "description": "Ensuring patients take prescribed heart failure medications correctly is crucial for symptom management.", "symptom_type": "general", "severity_threshold": 2, "priority": "medium", "instructions": "Review all medications with your clinician and discuss any challenges with taking them as prescribed. Consider utilizing medication organizers or reminders."}, {"id": "emergency_breathlessness", "title": "Severe Breathlessness - Seek Emergency Care", "description": "Rapidly worsening or severe shortness of breath may signal acute heart failure decompensation requiring urgent treatment.", "symptom_type": "dyspnea", "severity_threshold": 7, "priority": "urgent", "instructions": "If you experience sudden, severe worsening of shortness of breath at rest that does not improve with positioning and oxygen, call emergency services immediately."}, {"id": "emergency_edema", "title": "Severe Edema - Seek Emergency Care", "description": "Sudden onset of severe, widespread edema can indicate acute heart failure decompensation requiring urgent care.", "symptom_type": "edema", "severity_threshold": 7, "priority": "urgent", "instructions": "If you develop rapid swelling of multiple areas like abdomen, legs and arms, as well as shortness of breath, seek emergency care right away."}]	t	2025-04-01 01:42:33.118654	2025-04-01 01:42:33.118657
6	COPD Protocol	Protocol for patients with advanced COPD, focusing on respiratory symptoms, oxygen use, breathlessness, and breathing techniques.	COPD	1.0.0	[{"id": "breathlessness_severity", "text": "On a scale of 0 to 10, with 0 being no breathlessness and 10 being the worst breathlessness imaginable, how would you rate your current level of breathlessness?", "type": "numeric", "required": true, "symptom_type": "dyspnea", "min_value": 0, "max_value": 10, "category": "Respiratory Symptoms"}, {"id": "breathlessness_triggers", "text": "What activities or situations tend to make your breathlessness worse?", "type": "text", "required": true, "symptom_type": "dyspnea", "category": "Respiratory Symptoms"}, {"id": "breathlessness_patterns", "text": "Is your breathlessness constant or does it come and go in episodes?", "type": "choice", "required": true, "symptom_type": "dyspnea", "choices": ["Constant", "Episodes"], "category": "Respiratory Symptoms"}, {"id": "cough_frequency", "text": "How often do you experience coughing fits or spells?", "type": "choice", "required": true, "symptom_type": "cough", "choices": ["Rarely", "Few times a day", "Many times a day", "Constantly"], "category": "Respiratory Symptoms"}, {"id": "cough_productivity", "text": "Is your cough productive (bringing up sputum or phlegm)?", "type": "boolean", "required": true, "symptom_type": "cough", "category": "Respiratory Symptoms"}, {"id": "sputum_color", "text": "If your cough is productive, what color is the sputum or phlegm?", "type": "choice", "required": false, "symptom_type": "cough", "choices": ["Clear", "White/Gray", "Yellow/Green", "Brown", "Blood-tinged"], "category": "Respiratory Symptoms"}, {"id": "oxygen_use", "text": "Do you use supplemental oxygen?", "type": "boolean", "required": true, "symptom_type": "oxygen", "category": "Oxygen Therapy"}, {"id": "oxygen_effectiveness", "text": "On a scale of 0 to 10, with 0 being not effective at all and 10 being completely effective, how well does your oxygen therapy relieve your breathlessness?", "type": "numeric", "required": false, "symptom_type": "oxygen", "min_value": 0, "max_value": 10, "category": "Oxygen Therapy"}, {"id": "activity_tolerance", "text": "What types of activities are you able to do without becoming severely breathless?", "type": "text", "required": true, "symptom_type": "activity", "category": "Activity and Function"}, {"id": "sleep_quality", "text": "On a scale of 0 to 10, with 0 being very poor and 10 being excellent, how would you rate the quality of your sleep?", "type": "numeric", "required": true, "symptom_type": "sleep", "min_value": 0, "max_value": 10, "category": "Activity and Function"}, {"id": "sleep_positioning", "text": "Do you need to sleep in a certain position (such as upright or with extra pillows) to breathe more comfortably?", "type": "boolean", "required": true, "symptom_type": "sleep", "category": "Activity and Function"}, {"id": "respiratory_infection_signs", "text": "Have you noticed any signs that may indicate a respiratory infection, such as increased sputum production, fever, or worsening breathlessness?", "type": "boolean", "required": true, "symptom_type": "infection", "category": "Respiratory Symptoms"}, {"id": "medication_use", "text": "Are you taking any medications for your COPD, such as inhalers or nebulizer treatments?", "type": "boolean", "required": true, "symptom_type": "medication", "category": "Medication Management"}, {"id": "inhaler_technique", "text": "If you use inhalers, can you describe how you use them and if you have any concerns about your technique?", "type": "text", "required": false, "symptom_type": "medication", "category": "Medication Management"}, {"id": "anxiety_breathing", "text": "On a scale of 0 to 10, with 0 being no anxiety and 10 being severe anxiety, how much anxiety or panic do you experience related to your breathing difficulties?", "type": "numeric", "required": true, "symptom_type": "anxiety", "min_value": 0, "max_value": 10, "category": "Emotional Well-being"}, {"id": "adl_support_needs", "text": "Do you need any assistance with activities of daily living, such as bathing, dressing, or meal preparation, due to your breathing difficulties?", "type": "boolean", "required": true, "symptom_type": "function", "category": "Activity and Function"}]	[{"id": "node_breathlessness_severe", "symptom_type": "dyspnea", "condition": ">=", "value": 8, "next_node_id": "node_oxygen_intervention", "intervention_ids": []}, {"id": "node_oxygen_intervention", "symptom_type": "oxygen", "condition": "==", "value": true, "next_node_id": "node_oxygen_effectiveness", "intervention_ids": ["urgent_oxygen_intervention"]}, {"id": "node_oxygen_effectiveness", "symptom_type": "oxygen", "condition": "<=", "value": 3, "next_node_id": "node_exacerbation", "intervention_ids": ["oxygen_optimization"]}, {"id": "node_exacerbation", "symptom_type": "infection", "condition": "==", "value": true, "next_node_id": null, "intervention_ids": ["exacerbation_recognition", "secretion_clearance"]}, {"id": "node_breathlessness_moderate", "symptom_type": "dyspnea", "condition": ">=", "value": 5, "next_node_id": "node_anxiety_severe", "intervention_ids": ["pursed_lip_breathing", "diaphragmatic_breathing", "upright_positioning"]}, {"id": "node_anxiety_severe", "symptom_type": "anxiety", "condition": ">=", "value": 7, "next_node_id": null, "intervention_ids": ["anxiety_management", "anxiety_medication"]}, {"id": "node_breathlessness_mild", "symptom_type": "dyspnea", "condition": "<", "value": 5, "next_node_id": "node_cough_frequency", "intervention_ids": ["energy_conservation", "environmental_modifications"]}, {"id": "node_cough_frequency", "symptom_type": "cough", "condition": "==", "value": "Many times a day", "next_node_id": "node_cough_productivity", "intervention_ids": []}, {"id": "node_cough_productivity", "symptom_type": "cough", "condition": "==", "value": true, "next_node_id": "node_sputum_color", "intervention_ids": ["secretion_clearance"]}, {"id": "node_sputum_color", "symptom_type": "cough", "condition": "==", "value": "Yellow/Green", "next_node_id": null, "intervention_ids": ["exacerbation_recognition"]}, {"id": "node_sleep_quality", "symptom_type": "sleep", "condition": "<=", "value": 4, "next_node_id": "node_sleep_positioning", "intervention_ids": []}, {"id": "node_sleep_positioning", "symptom_type": "sleep", "condition": "==", "value": true, "next_node_id": null, "intervention_ids": ["upright_positioning"]}, {"id": "node_medication_use", "symptom_type": "medication", "condition": "==", "value": true, "next_node_id": "node_inhaler_technique", "intervention_ids": []}, {"id": "node_inhaler_technique", "symptom_type": "medication", "condition": "contains", "value": "concern", "next_node_id": null, "intervention_ids": ["inhaler_technique"]}, {"id": "node_function_impairment", "symptom_type": "function", "condition": "==", "value": true, "next_node_id": null, "intervention_ids": ["energy_conservation"]}]	[{"id": "pursed_lip_breathing", "title": "Pursed Lip Breathing", "description": "A breathing technique that helps control shortness of breath and keeps the airways open longer. Exhale slowly through pursed lips to prolong exhalation and prevent air trapping.", "symptom_type": "dyspnea", "severity_threshold": 2, "priority": "medium", "instructions": "Inhale slowly through your nose, then exhale slowly through pursed lips as if you're blowing out a candle. Exhale for twice as long as you inhale."}, {"id": "diaphragmatic_breathing", "title": "Diaphragmatic Breathing", "description": "A technique that promotes deeper, more efficient breathing by engaging the diaphragm muscle.", "symptom_type": "dyspnea", "severity_threshold": 2, "priority": "medium", "instructions": "Place one hand on your upper chest and the other on your abdomen. Inhale slowly through your nose, focusing on pushing your abdomen out. Exhale slowly through pursed lips, allowing your abdomen to fall inward."}, {"id": "upright_positioning", "title": "Upright Positioning", "description": "Sitting upright or leaning forward can help maximize lung expansion and ease breathing.", "symptom_type": "dyspnea", "severity_threshold": 3, "priority": "high", "instructions": "Sit upright in a chair or elevate the head of your bed. Lean forward with your arms resting on a table or your knees. Avoid lying flat."}, {"id": "energy_conservation", "title": "Energy Conservation Strategies", "description": "Techniques to reduce oxygen demand and avoid unnecessary exertion.", "symptom_type": "dyspnea", "severity_threshold": 2, "priority": "medium", "instructions": "Pace your activities, take breaks, use assistive devices, avoid strenuous tasks, and organize your environment to minimize exertion."}, {"id": "oxygen_optimization", "title": "Oxygen Therapy Optimization", "description": "Ensuring proper oxygen flow rate, delivery device, and adherence to therapy.", "symptom_type": "dyspnea", "severity_threshold": 4, "priority": "high", "instructions": "Check oxygen flow rate and adjust as prescribed. Ensure the delivery device (nasal cannula, mask) fits properly. Encourage adherence to oxygen therapy."}, {"id": "anxiety_management", "title": "Anxiety Management for Breathlessness", "description": "Techniques to reduce anxiety and promote relaxation during episodes of breathlessness.", "symptom_type": "dyspnea", "severity_threshold": 4, "priority": "high", "instructions": "Practice relaxation techniques like deep breathing, visualization, or progressive muscle relaxation. Use calming self-talk and distraction techniques."}, {"id": "secretion_clearance", "title": "Secretion Clearance Techniques", "description": "Methods to help mobilize and clear respiratory secretions.", "symptom_type": "dyspnea", "severity_threshold": 3, "priority": "medium", "instructions": "Use controlled coughing, deep breathing exercises, and postural drainage techniques. Stay hydrated and consider mucolytics if prescribed."}, {"id": "inhaler_technique", "title": "Inhaler Technique Optimization", "description": "Ensuring proper use of inhalers for maximum medication delivery and effectiveness.", "symptom_type": "dyspnea", "severity_threshold": 2, "priority": "medium", "instructions": "Review and demonstrate the correct inhaler technique, including preparation, inhalation, and breath-holding. Coordinate inhaler use with breathing techniques."}, {"id": "exacerbation_recognition", "title": "Recognition and Early Management of Exacerbations", "description": "Identifying and addressing exacerbations of COPD promptly to prevent further deterioration.", "symptom_type": "dyspnea", "severity_threshold": 4, "priority": "high", "instructions": "Watch for increased shortness of breath, cough, sputum production, or fever. Start prescribed rescue medications and follow your action plan. Seek medical attention if symptoms worsen or do not improve."}, {"id": "environmental_modifications", "title": "Environmental Modifications", "description": "Adjustments to the living space to reduce respiratory irritants and optimize air quality.", "symptom_type": "dyspnea", "severity_threshold": 2, "priority": "medium", "instructions": "Avoid exposure to smoke, dust, and strong odors. Use air purifiers, avoid aerosol products, and maintain proper ventilation."}, {"id": "urgent_oxygen_intervention", "title": "Urgent Oxygen Intervention", "description": "Immediate oxygen therapy adjustment for severe breathlessness or hypoxemia.", "symptom_type": "dyspnea", "severity_threshold": 5, "priority": "urgent", "instructions": "Increase oxygen flow rate to the maximum prescribed level. Switch to a higher-concentration delivery device (e.g., non-rebreather mask). Seek emergency medical attention if symptoms do not improve."}, {"id": "anxiety_medication", "title": "Anxiety Medication", "description": "Pharmacological intervention for severe anxiety associated with breathlessness.", "symptom_type": "dyspnea", "severity_threshold": 5, "priority": "high", "instructions": "Take prescribed anxiolytic medication as directed. Monitor for side effects and seek medical advice if anxiety persists or worsens."}, {"id": "secretion_suctioning", "title": "Secretion Suctioning", "description": "Removal of excessive respiratory secretions through suctioning.", "symptom_type": "dyspnea", "severity_threshold": 4, "priority": "high", "instructions": "If secretions are excessive and cannot be cleared through coughing or other techniques, contact your healthcare provider for suctioning assistance."}]	t	2025-04-01 01:43:34.167418	2025-04-01 01:43:34.167421
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: pallcare
--

COPY public.users (id, username, email, password, first_name, last_name, role, phone_number, license_number, is_active, login_attempts, last_login_at, created_at, updated_at) FROM stdin;
27	nurse2	nurse2@example.com	$2b$04$Gbde4mHJJMKvfNkjaKZ2xedturot4y705G2FciFd2RLPTEMFbUgBy	Robert	Johnson	NURSE	555-345-6789	RN67890	t	0	\N	2025-04-02 18:38:56.0849	2025-04-02 18:38:56.084901
28	physician	physician@example.com	$2b$04$2WsgpUdPPxjbMPEWrz6loe6k.4XSW0dilY9BWk.2NzinNh4necvb2	Sarah	Williams	PHYSICIAN	555-456-7890	MD12345	t	0	2025-04-06 04:05:34.102029	2025-04-02 18:38:56.084901	2025-04-06 04:05:34.102298
26	nurse1	nurse1@example.com	$2b$04$cQgvcUWOGaCsqyM1hmOyNOb7Lrd4o.EXQU6yBQqNP3Ecs3LgOTXla	Jane	Smith	NURSE	555-234-5678	RN12345	t	0	2025-04-06 04:06:04.136225	2025-04-02 18:38:56.0849	2025-04-06 04:06:04.136389
25	admin	admin@example.com	$2b$04$ETDfV1vMz2CqcV5ktS752.wPeov9MXHKOA5Ughp1vJ3z0TMooW7Ti	Admin	User	ADMIN	555-123-4567	\N	t	0	2025-04-16 01:58:53.798888	2025-04-02 18:38:56.084898	2025-04-16 01:58:53.800082
\.


--
-- Name: assessments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pallcare
--

SELECT pg_catalog.setval('public.assessments_id_seq', 147, true);


--
-- Name: audit_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pallcare
--

SELECT pg_catalog.setval('public.audit_logs_id_seq', 184, true);


--
-- Name: calls_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pallcare
--

SELECT pg_catalog.setval('public.calls_id_seq', 28, true);


--
-- Name: medications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pallcare
--

SELECT pg_catalog.setval('public.medications_id_seq', 28, true);


--
-- Name: patients_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pallcare
--

SELECT pg_catalog.setval('public.patients_id_seq', 21, true);


--
-- Name: protocols_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pallcare
--

SELECT pg_catalog.setval('public.protocols_id_seq', 6, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pallcare
--

SELECT pg_catalog.setval('public.users_id_seq', 28, true);


--
-- Name: assessments assessments_pkey; Type: CONSTRAINT; Schema: public; Owner: pallcare
--

ALTER TABLE ONLY public.assessments
    ADD CONSTRAINT assessments_pkey PRIMARY KEY (id);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: pallcare
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: calls calls_pkey; Type: CONSTRAINT; Schema: public; Owner: pallcare
--

ALTER TABLE ONLY public.calls
    ADD CONSTRAINT calls_pkey PRIMARY KEY (id);


--
-- Name: medications medications_pkey; Type: CONSTRAINT; Schema: public; Owner: pallcare
--

ALTER TABLE ONLY public.medications
    ADD CONSTRAINT medications_pkey PRIMARY KEY (id);


--
-- Name: patients patients_pkey; Type: CONSTRAINT; Schema: public; Owner: pallcare
--

ALTER TABLE ONLY public.patients
    ADD CONSTRAINT patients_pkey PRIMARY KEY (id);


--
-- Name: protocols protocols_pkey; Type: CONSTRAINT; Schema: public; Owner: pallcare
--

ALTER TABLE ONLY public.protocols
    ADD CONSTRAINT protocols_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: pallcare
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_patients_mrn; Type: INDEX; Schema: public; Owner: pallcare
--

CREATE UNIQUE INDEX ix_patients_mrn ON public.patients USING btree (mrn);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: pallcare
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: pallcare
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: assessments assessments_call_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pallcare
--

ALTER TABLE ONLY public.assessments
    ADD CONSTRAINT assessments_call_id_fkey FOREIGN KEY (call_id) REFERENCES public.calls(id);


--
-- Name: assessments assessments_conducted_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pallcare
--

ALTER TABLE ONLY public.assessments
    ADD CONSTRAINT assessments_conducted_by_id_fkey FOREIGN KEY (conducted_by_id) REFERENCES public.users(id);


--
-- Name: assessments assessments_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pallcare
--

ALTER TABLE ONLY public.assessments
    ADD CONSTRAINT assessments_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: assessments assessments_protocol_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pallcare
--

ALTER TABLE ONLY public.assessments
    ADD CONSTRAINT assessments_protocol_id_fkey FOREIGN KEY (protocol_id) REFERENCES public.protocols(id);


--
-- Name: audit_logs audit_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pallcare
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: calls calls_conducted_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pallcare
--

ALTER TABLE ONLY public.calls
    ADD CONSTRAINT calls_conducted_by_id_fkey FOREIGN KEY (conducted_by_id) REFERENCES public.users(id);


--
-- Name: calls calls_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pallcare
--

ALTER TABLE ONLY public.calls
    ADD CONSTRAINT calls_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: medications medications_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pallcare
--

ALTER TABLE ONLY public.medications
    ADD CONSTRAINT medications_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: patients patients_primary_nurse_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pallcare
--

ALTER TABLE ONLY public.patients
    ADD CONSTRAINT patients_primary_nurse_id_fkey FOREIGN KEY (primary_nurse_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--

