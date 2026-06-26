--
-- PostgreSQL database dump
--

\restrict 2ggsVh9547S3B9ADWQ2lAAgavGHQd0Em8PYe3n3Gs0cYOrq1CLrP6YkIbBMIeqs

-- Dumped from database version 16.14
-- Dumped by pg_dump version 16.14

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
-- Name: chargestatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.chargestatus AS ENUM (
    'PAID',
    'PARTIAL',
    'UNPAID'
);


--
-- Name: customchargestatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.customchargestatus AS ENUM (
    'PAID',
    'PARTIAL',
    'UNPAID'
);


--
-- Name: expensestatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.expensestatus AS ENUM (
    'pending',
    'paid',
    'cancelled'
);


--
-- Name: expensetype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.expensetype AS ENUM (
    'repair',
    'maintenance',
    'utility',
    'administrative',
    'cleaning',
    'elevator',
    'security',
    'insurance',
    'other'
);


--
-- Name: obligationstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.obligationstatus AS ENUM (
    'PAID',
    'PARTIAL',
    'UNPAID'
);


--
-- Name: obligationtype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.obligationtype AS ENUM (
    'MONTHLY',
    'INITIAL',
    'PENALTY',
    'REPAIR',
    'FUND',
    'OTHER'
);


--
-- Name: transactionreference; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.transactionreference AS ENUM (
    'PAYMENT',
    'OBLIGATION',
    'ADJUSTMENT',
    'MIGRATION'
);


--
-- Name: transactiontype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.transactiontype AS ENUM (
    'CREDIT',
    'DEBIT'
);


--
-- Name: userrole; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.userrole AS ENUM (
    'ADMIN',
    'CASHIER',
    'VIEWER'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: account_transactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.account_transactions (
    id integer NOT NULL,
    account_id integer NOT NULL,
    type public.transactiontype NOT NULL,
    amount numeric(10,2) NOT NULL,
    reference_type public.transactionreference NOT NULL,
    reference_id integer,
    balance_after numeric(10,2) NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: COLUMN account_transactions.account_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.account_transactions.account_id IS 'ID на сметката';


--
-- Name: COLUMN account_transactions.type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.account_transactions.type IS 'Тип на транзакцията (credit/debit)';


--
-- Name: COLUMN account_transactions.amount; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.account_transactions.amount IS 'Сума на транзакцията в лева';


--
-- Name: COLUMN account_transactions.reference_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.account_transactions.reference_type IS 'Тип на източника (payment/obligation/adjustment)';


--
-- Name: COLUMN account_transactions.reference_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.account_transactions.reference_id IS 'ID на свързания запис (payment_id, obligation_id и т.н.)';


--
-- Name: COLUMN account_transactions.balance_after; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.account_transactions.balance_after IS 'Баланс на сметката след транзакцията';


--
-- Name: COLUMN account_transactions.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.account_transactions.description IS 'Описание на транзакцията';


--
-- Name: COLUMN account_transactions.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.account_transactions.created_at IS 'Дата на създаване';


--
-- Name: COLUMN account_transactions.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.account_transactions.updated_at IS 'Дата на последна промяна';


--
-- Name: account_transactions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.account_transactions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: account_transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.account_transactions_id_seq OWNED BY public.account_transactions.id;


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: apartment_accounts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.apartment_accounts (
    id integer NOT NULL,
    apartment_id integer NOT NULL,
    balance numeric(10,2) DEFAULT 0.00 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: COLUMN apartment_accounts.apartment_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.apartment_accounts.apartment_id IS 'ID на апартамента';


--
-- Name: COLUMN apartment_accounts.balance; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.apartment_accounts.balance IS 'Текущ баланс в лева (отрицателен = дължи)';


--
-- Name: COLUMN apartment_accounts.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.apartment_accounts.created_at IS 'Дата на създаване';


--
-- Name: COLUMN apartment_accounts.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.apartment_accounts.updated_at IS 'Дата на последна промяна';


--
-- Name: apartment_accounts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.apartment_accounts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: apartment_accounts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.apartment_accounts_id_seq OWNED BY public.apartment_accounts.id;


--
-- Name: apartments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.apartments (
    id integer NOT NULL,
    number character varying(20) NOT NULL,
    floor integer,
    owner_name character varying(200) NOT NULL,
    residents_count integer NOT NULL,
    monthly_fee numeric(10,2) NOT NULL,
    notes text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: COLUMN apartments.number; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.apartments.number IS 'Номер на апартамента (напр. ''1'', ''12А'')';


--
-- Name: COLUMN apartments.floor; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.apartments.floor IS 'Етаж (0 за партер, отрицателни за сутерен)';


--
-- Name: COLUMN apartments.owner_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.apartments.owner_name IS 'Име на собственика';


--
-- Name: COLUMN apartments.residents_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.apartments.residents_count IS 'Брой живущи в апартамента';


--
-- Name: COLUMN apartments.monthly_fee; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.apartments.monthly_fee IS 'Месечна такса в лева';


--
-- Name: COLUMN apartments.notes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.apartments.notes IS 'Допълнителни бележки';


--
-- Name: COLUMN apartments.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.apartments.created_at IS 'Дата на създаване';


--
-- Name: COLUMN apartments.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.apartments.updated_at IS 'Дата на последна промяна';


--
-- Name: apartments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.apartments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: apartments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.apartments_id_seq OWNED BY public.apartments.id;


--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_logs (
    id integer NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    action character varying(100) NOT NULL,
    user_id integer,
    user_email character varying(255),
    entity_type character varying(100),
    entity_id integer,
    apartment_id integer,
    description text NOT NULL,
    state_before json,
    state_after json,
    metadata json,
    ip_address character varying(45),
    is_critical boolean NOT NULL
);


--
-- Name: COLUMN audit_logs."timestamp"; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.audit_logs."timestamp" IS 'Exact timestamp when action occurred';


--
-- Name: COLUMN audit_logs.action; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.audit_logs.action IS 'Type of action performed';


--
-- Name: COLUMN audit_logs.user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.audit_logs.user_id IS 'User who performed the action';


--
-- Name: COLUMN audit_logs.user_email; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.audit_logs.user_email IS 'Email at time of action (denormalized)';


--
-- Name: COLUMN audit_logs.entity_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.audit_logs.entity_type IS 'Type of entity affected';


--
-- Name: COLUMN audit_logs.entity_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.audit_logs.entity_id IS 'ID of affected entity';


--
-- Name: COLUMN audit_logs.apartment_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.audit_logs.apartment_id IS 'Apartment context if applicable';


--
-- Name: COLUMN audit_logs.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.audit_logs.description IS 'Human-readable description';


--
-- Name: COLUMN audit_logs.state_before; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.audit_logs.state_before IS 'State before action';


--
-- Name: COLUMN audit_logs.state_after; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.audit_logs.state_after IS 'State after action';


--
-- Name: COLUMN audit_logs.metadata; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.audit_logs.metadata IS 'Additional context';


--
-- Name: COLUMN audit_logs.ip_address; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.audit_logs.ip_address IS 'IP address';


--
-- Name: COLUMN audit_logs.is_critical; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.audit_logs.is_critical IS 'Critical action flag';


--
-- Name: audit_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.audit_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: audit_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.audit_logs_id_seq OWNED BY public.audit_logs.id;


--
-- Name: expenses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.expenses (
    id integer NOT NULL,
    description character varying(500) NOT NULL,
    amount numeric(10,2) NOT NULL,
    expense_type public.expensetype NOT NULL,
    status public.expensestatus NOT NULL,
    expense_date timestamp without time zone NOT NULL,
    paid_date timestamp without time zone,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    vendor character varying(255),
    invoice_number character varying(100),
    notes text,
    created_by integer
);


--
-- Name: expenses_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.expenses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: expenses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.expenses_id_seq OWNED BY public.expenses.id;


--
-- Name: obligations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.obligations (
    id integer NOT NULL,
    type public.obligationtype NOT NULL,
    apartment_id integer NOT NULL,
    month character varying(7),
    description text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    amount numeric(10,2) NOT NULL
);


--
-- Name: COLUMN obligations.type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.obligations.type IS 'Тип на задължението';


--
-- Name: COLUMN obligations.apartment_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.obligations.apartment_id IS 'ID на апартамента';


--
-- Name: COLUMN obligations.month; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.obligations.month IS 'Месец на задължението (YYYY-MM), само за месечни такси';


--
-- Name: COLUMN obligations.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.obligations.description IS 'Описание на задължението';


--
-- Name: COLUMN obligations.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.obligations.created_at IS 'Дата на създаване';


--
-- Name: COLUMN obligations.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.obligations.updated_at IS 'Дата на последна промяна';


--
-- Name: COLUMN obligations.amount; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.obligations.amount IS 'Сума на задължението в лева';


--
-- Name: obligations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.obligations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: obligations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.obligations_id_seq OWNED BY public.obligations.id;


--
-- Name: payments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payments (
    id integer NOT NULL,
    apartment_id integer NOT NULL,
    amount numeric(10,2) NOT NULL,
    month character varying(7) NOT NULL,
    payment_date date NOT NULL,
    payment_method character varying(50) NOT NULL,
    collected_by_id integer,
    notes text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    status character varying(20) DEFAULT 'active'::character varying NOT NULL,
    voided_at timestamp without time zone,
    voided_by_id integer,
    void_reason text
);


--
-- Name: COLUMN payments.apartment_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.payments.apartment_id IS 'ID на апартамента';


--
-- Name: COLUMN payments.amount; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.payments.amount IS 'Платена сума в лева';


--
-- Name: COLUMN payments.month; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.payments.month IS 'Месец за плащането (YYYY-MM)';


--
-- Name: COLUMN payments.payment_date; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.payments.payment_date IS 'Дата на плащане';


--
-- Name: COLUMN payments.payment_method; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.payments.payment_method IS 'Метод на плащане (cash, bank, card)';


--
-- Name: COLUMN payments.collected_by_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.payments.collected_by_id IS 'ID на касиера приел плащането';


--
-- Name: COLUMN payments.notes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.payments.notes IS 'Допълнителни бележки';


--
-- Name: COLUMN payments.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.payments.created_at IS 'Дата на създаване';


--
-- Name: COLUMN payments.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.payments.updated_at IS 'Дата на последна промяна';


--
-- Name: COLUMN payments.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.payments.status IS 'Статус: active, voided, refunded';


--
-- Name: COLUMN payments.voided_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.payments.voided_at IS 'Кога е анулирано плащането';


--
-- Name: COLUMN payments.voided_by_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.payments.voided_by_id IS 'ID на потребителя анулирал плащането';


--
-- Name: COLUMN payments.void_reason; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.payments.void_reason IS 'Причина за анулиране (задължително)';


--
-- Name: payments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.payments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: payments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.payments_id_seq OWNED BY public.payments.id;


--
-- Name: receipts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.receipts (
    id integer NOT NULL,
    receipt_number character varying(20) NOT NULL,
    payment_id integer NOT NULL,
    is_copy boolean NOT NULL,
    original_receipt_id integer,
    issued_at timestamp without time zone NOT NULL,
    issued_by_id integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: COLUMN receipts.receipt_number; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.receipts.receipt_number IS 'Номер на разписката (YYYY-NNNNNN)';


--
-- Name: COLUMN receipts.payment_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.receipts.payment_id IS 'ID на плащането';


--
-- Name: COLUMN receipts.is_copy; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.receipts.is_copy IS 'Дали е копие (True) или оригинал (False)';


--
-- Name: COLUMN receipts.original_receipt_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.receipts.original_receipt_id IS 'ID на оригиналната разписка (само за копия)';


--
-- Name: COLUMN receipts.issued_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.receipts.issued_at IS 'Дата и час на издаване';


--
-- Name: COLUMN receipts.issued_by_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.receipts.issued_by_id IS 'ID на потребителя издал разписката';


--
-- Name: COLUMN receipts.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.receipts.created_at IS 'Дата на създаване';


--
-- Name: COLUMN receipts.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.receipts.updated_at IS 'Дата на последна промяна';


--
-- Name: receipts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.receipts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: receipts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.receipts_id_seq OWNED BY public.receipts.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(100) NOT NULL,
    password_hash character varying(255) NOT NULL,
    display_name character varying(200) NOT NULL,
    role public.userrole NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: COLUMN users.username; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.username IS 'Потребителско име за вход';


--
-- Name: COLUMN users.password_hash; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.password_hash IS 'Хеширана парола';


--
-- Name: COLUMN users.display_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.display_name IS 'Име за показване (напр. ''Цецка'')';


--
-- Name: COLUMN users.role; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.role IS 'Роля на потребителя';


--
-- Name: COLUMN users.is_active; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.is_active IS 'Дали потребителят е активен';


--
-- Name: COLUMN users.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.created_at IS 'Дата на създаване';


--
-- Name: COLUMN users.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.updated_at IS 'Дата на последна промяна';


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: account_transactions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.account_transactions ALTER COLUMN id SET DEFAULT nextval('public.account_transactions_id_seq'::regclass);


--
-- Name: apartment_accounts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.apartment_accounts ALTER COLUMN id SET DEFAULT nextval('public.apartment_accounts_id_seq'::regclass);


--
-- Name: apartments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.apartments ALTER COLUMN id SET DEFAULT nextval('public.apartments_id_seq'::regclass);


--
-- Name: audit_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs ALTER COLUMN id SET DEFAULT nextval('public.audit_logs_id_seq'::regclass);


--
-- Name: expenses id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expenses ALTER COLUMN id SET DEFAULT nextval('public.expenses_id_seq'::regclass);


--
-- Name: obligations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.obligations ALTER COLUMN id SET DEFAULT nextval('public.obligations_id_seq'::regclass);


--
-- Name: payments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments ALTER COLUMN id SET DEFAULT nextval('public.payments_id_seq'::regclass);


--
-- Name: receipts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.receipts ALTER COLUMN id SET DEFAULT nextval('public.receipts_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: account_transactions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.account_transactions (id, account_id, type, amount, reference_type, reference_id, balance_after, description, created_at, updated_at) FROM stdin;
1	1	DEBIT	55.00	OBLIGATION	1	-55.00	initial задължение	2026-06-25 11:18:19.180126+00	2026-06-25 11:18:19.180126+00
2	8	DEBIT	214.00	OBLIGATION	2	-214.00	initial задължение	2026-06-25 11:18:41.201187+00	2026-06-25 11:18:41.201187+00
3	13	DEBIT	42.00	OBLIGATION	3	-42.00	initial задължение	2026-06-25 11:18:53.503281+00	2026-06-25 11:18:53.503281+00
4	18	DEBIT	68.00	OBLIGATION	4	-68.00	initial задължение	2026-06-25 11:19:13.807408+00	2026-06-25 11:19:13.807408+00
5	19	DEBIT	55.00	OBLIGATION	5	-55.00	initial задължение	2026-06-25 11:19:31.99278+00	2026-06-25 11:19:31.99278+00
6	2	DEBIT	70.00	OBLIGATION	6	-70.00	initial задължение	2026-06-25 11:20:02.444135+00	2026-06-25 11:20:02.444135+00
7	3	DEBIT	42.00	OBLIGATION	7	-42.00	initial задължение	2026-06-25 11:20:18.61412+00	2026-06-25 11:20:18.61412+00
8	4	DEBIT	68.00	OBLIGATION	8	-68.00	initial задължение	2026-06-25 11:20:33.060766+00	2026-06-25 11:20:33.060766+00
9	5	DEBIT	175.00	OBLIGATION	9	-175.00	initial задължение	2026-06-25 11:20:58.867231+00	2026-06-25 11:20:58.867231+00
10	6	DEBIT	70.00	OBLIGATION	10	-70.00	initial задължение	2026-06-25 11:21:15.628139+00	2026-06-25 11:21:15.628139+00
11	7	DEBIT	42.00	OBLIGATION	11	-42.00	initial задължение	2026-06-25 11:21:27.412376+00	2026-06-25 11:21:27.412376+00
12	9	DEBIT	68.00	OBLIGATION	12	-68.00	initial задължение	2026-06-25 11:21:41.616716+00	2026-06-25 11:21:41.616716+00
13	10	DEBIT	55.00	OBLIGATION	13	-55.00	initial задължение	2026-06-25 11:21:55.035243+00	2026-06-25 11:21:55.035243+00
14	11	DEBIT	70.00	OBLIGATION	14	-70.00	initial задължение	2026-06-25 11:22:16.955041+00	2026-06-25 11:22:16.955041+00
15	12	DEBIT	42.00	OBLIGATION	15	-42.00	initial задължение	2026-06-25 11:22:27.446696+00	2026-06-25 11:22:27.446696+00
16	20	DEBIT	68.00	OBLIGATION	16	-68.00	initial задължение	2026-06-25 11:23:27.285471+00	2026-06-25 11:23:27.285471+00
17	14	DEBIT	55.00	OBLIGATION	17	-55.00	initial задължение	2026-06-25 11:23:40.582435+00	2026-06-25 11:23:40.582435+00
18	15	DEBIT	70.00	OBLIGATION	18	-70.00	initial задължение	2026-06-25 11:23:52.964874+00	2026-06-25 11:23:52.964874+00
19	16	DEBIT	42.00	OBLIGATION	19	-42.00	initial задължение	2026-06-25 11:24:04.439427+00	2026-06-25 11:24:04.439427+00
20	17	DEBIT	188.00	OBLIGATION	20	-188.00	initial задължение	2026-06-25 11:24:25.858031+00	2026-06-25 11:24:25.858031+00
21	11	CREDIT	10.00	PAYMENT	1	-60.00	Плащане за 2026-06	2026-06-25 14:39:50.78397+00	2026-06-25 14:39:50.78397+00
22	11	CREDIT	10.00	PAYMENT	2	-50.00	Плащане за 2026-06	2026-06-26 05:32:13.932026+00	2026-06-26 05:32:13.932026+00
\.


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.alembic_version (version_num) FROM stdin;
f7g8h9i0j1k2
\.


--
-- Data for Name: apartment_accounts; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.apartment_accounts (id, apartment_id, balance, created_at, updated_at) FROM stdin;
1	1	-55.00	2026-06-25 11:15:32.332273+00	2026-06-25 11:18:19.180126+00
8	2	-214.00	2026-06-25 11:15:32.416672+00	2026-06-25 11:18:41.201187+00
13	3	-42.00	2026-06-25 11:15:32.460567+00	2026-06-25 11:18:53.503281+00
18	4	-68.00	2026-06-25 11:15:32.503737+00	2026-06-25 11:19:13.807408+00
19	5	-55.00	2026-06-25 11:15:32.512403+00	2026-06-25 11:19:31.99278+00
2	6	-70.00	2026-06-25 11:15:32.348728+00	2026-06-25 11:20:02.444135+00
3	7	-42.00	2026-06-25 11:15:32.36434+00	2026-06-25 11:20:18.61412+00
4	8	-68.00	2026-06-25 11:15:32.376573+00	2026-06-25 11:20:33.060766+00
5	9	-175.00	2026-06-25 11:15:32.387066+00	2026-06-25 11:20:58.867231+00
6	10	-70.00	2026-06-25 11:15:32.398228+00	2026-06-25 11:21:15.628139+00
7	11	-42.00	2026-06-25 11:15:32.408024+00	2026-06-25 11:21:27.412376+00
9	12	-68.00	2026-06-25 11:15:32.42575+00	2026-06-25 11:21:41.616716+00
10	13	-55.00	2026-06-25 11:15:32.434505+00	2026-06-25 11:21:55.035243+00
12	15	-42.00	2026-06-25 11:15:32.451857+00	2026-06-25 11:22:27.446696+00
20	20	-68.00	2026-06-25 11:23:15.923287+00	2026-06-25 11:23:27.285471+00
14	16	-55.00	2026-06-25 11:15:32.469459+00	2026-06-25 11:23:40.582435+00
15	17	-70.00	2026-06-25 11:15:32.477616+00	2026-06-25 11:23:52.964874+00
16	18	-42.00	2026-06-25 11:15:32.486438+00	2026-06-25 11:24:04.439427+00
17	19	-188.00	2026-06-25 11:15:32.494717+00	2026-06-25 11:24:25.858031+00
11	14	-50.00	2026-06-25 11:15:32.443427+00	2026-06-26 05:32:13.932026+00
\.


--
-- Data for Name: apartments; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.apartments (id, number, floor, owner_name, residents_count, monthly_fee, notes, created_at, updated_at) FROM stdin;
1	1	1	Драгана	1	9.00	\N	2026-06-25 11:02:39.779907+00	2026-06-25 11:02:39.779907+00
2	2	1	Огнян	2	11.00	\N	2026-06-25 11:02:56.84957+00	2026-06-25 11:02:56.84957+00
4	4	1	Георги	2	11.00	\N	2026-06-25 11:03:41.48201+00	2026-06-25 11:03:41.48201+00
6	10	2	Петия	1	9.00	\N	2026-06-25 11:05:36.119746+00	2026-06-25 11:05:36.119746+00
7	11	2	Венета	1	9.00	\N	2026-06-25 11:05:59.960006+00	2026-06-25 11:05:59.960006+00
8	12	2	Петър Спасов	1	9.00	\N	2026-06-25 11:06:18.543712+00	2026-06-25 11:06:18.543712+00
10	18	3	Надка Чуканова	2	11.00	\N	2026-06-25 11:06:50.503613+00	2026-06-25 11:06:50.503613+00
12	20	3	Ивайло Крумов	3	13.00	\N	2026-06-25 11:10:31.447569+00	2026-06-25 11:10:31.447569+00
13	25	4	Радослав 	2	11.00	\N	2026-06-25 11:11:46.672094+00	2026-06-25 11:11:46.672094+00
9	17	3	Ивка	1	9.50	0.5 за куче	2026-06-25 11:06:32.675583+00	2026-06-25 11:11:59.689047+00
14	26	4	Георги Данчев	2	13.50	+ 2 деца + куче	2026-06-25 11:12:27.686697+00	2026-06-25 11:12:27.686697+00
15	27	4	Диляна Чипилова	1	9.00	\N	2026-06-25 11:12:46.902111+00	2026-06-25 11:12:46.902111+00
17	34	5	Тодорка	1	11.00	+ 2 деца	2026-06-25 11:14:22.509691+00	2026-06-25 11:14:22.509691+00
18	35	5	Бисерка	1	9.50	+ куче	2026-06-25 11:14:53.043906+00	2026-06-25 11:14:53.043906+00
19	36	5	Мирослава	1	9.00	\N	2026-06-25 11:15:09.296145+00	2026-06-25 11:15:09.296145+00
11	19	3	Цецка Бенчева	0	7.00	\N	2026-06-25 11:08:18.879575+00	2026-06-25 11:15:26.056147+00
5	9	2	Цветослава Василева Ботева	0	7.00	\N	2026-06-25 11:05:23.747186+00	2026-06-25 11:16:40.111688+00
16	33	5	Цветелина Григорова 	1	9.00	\N	2026-06-25 11:13:46.067143+00	2026-06-25 11:16:53.803804+00
3	3	1	Стоянка Гълабова 	0	7.00	\N	2026-06-25 11:03:18.811383+00	2026-06-25 11:17:03.218571+00
20	28	4	Николай 	1	9.00	\N	2026-06-25 11:23:14.338377+00	2026-06-25 11:23:14.338377+00
\.


--
-- Data for Name: audit_logs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.audit_logs (id, "timestamp", action, user_id, user_email, entity_type, entity_id, apartment_id, description, state_before, state_after, metadata, ip_address, is_critical) FROM stdin;
\.


--
-- Data for Name: expenses; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.expenses (id, description, amount, expense_type, status, expense_date, paid_date, created_at, updated_at, vendor, invoice_number, notes, created_by) FROM stdin;
\.


--
-- Data for Name: obligations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.obligations (id, type, apartment_id, month, description, created_at, updated_at, amount) FROM stdin;
1	INITIAL	1	\N	\N	2026-06-25 11:18:19.180126+00	2026-06-25 11:18:19.180126+00	55.00
2	INITIAL	2	\N	\N	2026-06-25 11:18:41.201187+00	2026-06-25 11:18:41.201187+00	214.00
3	INITIAL	3	\N	\N	2026-06-25 11:18:53.503281+00	2026-06-25 11:18:53.503281+00	42.00
4	INITIAL	4	\N	\N	2026-06-25 11:19:13.807408+00	2026-06-25 11:19:13.807408+00	68.00
5	INITIAL	5	\N	\N	2026-06-25 11:19:31.99278+00	2026-06-25 11:19:31.99278+00	55.00
6	INITIAL	6	\N	\N	2026-06-25 11:20:02.444135+00	2026-06-25 11:20:02.444135+00	70.00
7	INITIAL	7	\N	\N	2026-06-25 11:20:18.61412+00	2026-06-25 11:20:18.61412+00	42.00
8	INITIAL	8	\N	\N	2026-06-25 11:20:33.060766+00	2026-06-25 11:20:33.060766+00	68.00
9	INITIAL	9	\N	\N	2026-06-25 11:20:58.867231+00	2026-06-25 11:20:58.867231+00	175.00
10	INITIAL	10	\N	\N	2026-06-25 11:21:15.628139+00	2026-06-25 11:21:15.628139+00	70.00
11	INITIAL	11	\N	\N	2026-06-25 11:21:27.412376+00	2026-06-25 11:21:27.412376+00	42.00
12	INITIAL	12	\N	\N	2026-06-25 11:21:41.616716+00	2026-06-25 11:21:41.616716+00	68.00
13	INITIAL	13	\N	\N	2026-06-25 11:21:55.035243+00	2026-06-25 11:21:55.035243+00	55.00
14	INITIAL	14	\N	\N	2026-06-25 11:22:16.955041+00	2026-06-25 11:22:16.955041+00	70.00
15	INITIAL	15	\N	\N	2026-06-25 11:22:27.446696+00	2026-06-25 11:22:27.446696+00	42.00
16	INITIAL	20	\N	\N	2026-06-25 11:23:27.285471+00	2026-06-25 11:23:27.285471+00	68.00
17	INITIAL	16	\N	\N	2026-06-25 11:23:40.582435+00	2026-06-25 11:23:40.582435+00	55.00
18	INITIAL	17	\N	\N	2026-06-25 11:23:52.964874+00	2026-06-25 11:23:52.964874+00	70.00
19	INITIAL	18	\N	\N	2026-06-25 11:24:04.439427+00	2026-06-25 11:24:04.439427+00	42.00
20	INITIAL	19	\N	\N	2026-06-25 11:24:25.858031+00	2026-06-25 11:24:25.858031+00	188.00
\.


--
-- Data for Name: payments; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.payments (id, apartment_id, amount, month, payment_date, payment_method, collected_by_id, notes, created_at, updated_at, status, voided_at, voided_by_id, void_reason) FROM stdin;
1	14	10.00	2026-06	2026-06-25	cash	2	\N	2026-06-25 14:39:50.78397+00	2026-06-25 14:39:50.78397+00	ACTIVE	\N	\N	\N
2	14	10.00	2026-06	2026-06-26	cash	2	\N	2026-06-26 05:32:13.932026+00	2026-06-26 05:32:13.932026+00	ACTIVE	\N	\N	\N
\.


--
-- Data for Name: receipts; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.receipts (id, receipt_number, payment_id, is_copy, original_receipt_id, issued_at, issued_by_id, created_at, updated_at) FROM stdin;
1	2026-000001	1	f	\N	2026-06-25 14:39:50.79622	2	2026-06-25 14:39:50.78397+00	2026-06-25 14:39:50.78397+00
2	2026-000002	2	f	\N	2026-06-26 05:32:13.937809	2	2026-06-26 05:32:13.932026+00	2026-06-26 05:32:13.932026+00
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users (id, username, password_hash, display_name, role, is_active, created_at, updated_at) FROM stdin;
1	admin	$2b$12$9WZXeq1QXH0rf4aXu5tt8eV.SnASm/BrBgR9mYUonSj506/wHlaR2	Администратор	ADMIN	t	2026-06-25 10:43:05.990124+00	2026-06-25 10:43:05.990124+00
2	cecka	$2b$12$M.rZPwz7mAkopTZ2k4yuJu326xPVNHk6mL1E3MpSKvOnoFb8199HS	Цецка	CASHIER	t	2026-06-25 10:43:05.990124+00	2026-06-25 10:43:05.990124+00
\.


--
-- Name: account_transactions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.account_transactions_id_seq', 22, true);


--
-- Name: apartment_accounts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.apartment_accounts_id_seq', 20, true);


--
-- Name: apartments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.apartments_id_seq', 20, true);


--
-- Name: audit_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.audit_logs_id_seq', 1, false);


--
-- Name: expenses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.expenses_id_seq', 1, false);


--
-- Name: obligations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.obligations_id_seq', 20, true);


--
-- Name: payments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.payments_id_seq', 2, true);


--
-- Name: receipts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.receipts_id_seq', 2, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.users_id_seq', 2, true);


--
-- Name: account_transactions account_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.account_transactions
    ADD CONSTRAINT account_transactions_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: apartment_accounts apartment_accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.apartment_accounts
    ADD CONSTRAINT apartment_accounts_pkey PRIMARY KEY (id);


--
-- Name: apartments apartments_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.apartments
    ADD CONSTRAINT apartments_number_key UNIQUE (number);


--
-- Name: apartments apartments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.apartments
    ADD CONSTRAINT apartments_pkey PRIMARY KEY (id);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: expenses expenses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_pkey PRIMARY KEY (id);


--
-- Name: obligations obligations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.obligations
    ADD CONSTRAINT obligations_pkey PRIMARY KEY (id);


--
-- Name: payments payments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_pkey PRIMARY KEY (id);


--
-- Name: receipts receipts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.receipts
    ADD CONSTRAINT receipts_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_account_transactions_account_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_account_transactions_account_id ON public.account_transactions USING btree (account_id);


--
-- Name: ix_apartment_accounts_apartment_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_apartment_accounts_apartment_id ON public.apartment_accounts USING btree (apartment_id);


--
-- Name: ix_audit_logs_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_action ON public.audit_logs USING btree (action);


--
-- Name: ix_audit_logs_apartment_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_apartment_id ON public.audit_logs USING btree (apartment_id);


--
-- Name: ix_audit_logs_entity_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_entity_id ON public.audit_logs USING btree (entity_id);


--
-- Name: ix_audit_logs_entity_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_entity_type ON public.audit_logs USING btree (entity_type);


--
-- Name: ix_audit_logs_is_critical; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_is_critical ON public.audit_logs USING btree (is_critical);


--
-- Name: ix_audit_logs_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_timestamp ON public.audit_logs USING btree ("timestamp");


--
-- Name: ix_audit_logs_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_user_id ON public.audit_logs USING btree (user_id);


--
-- Name: ix_expenses_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_expenses_id ON public.expenses USING btree (id);


--
-- Name: ix_obligations_apartment_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_obligations_apartment_id ON public.obligations USING btree (apartment_id);


--
-- Name: ix_obligations_month; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_obligations_month ON public.obligations USING btree (month);


--
-- Name: ix_obligations_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_obligations_type ON public.obligations USING btree (type);


--
-- Name: ix_payments_apartment_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_payments_apartment_id ON public.payments USING btree (apartment_id);


--
-- Name: ix_payments_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_payments_status ON public.payments USING btree (status);


--
-- Name: ix_receipts_payment_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_receipts_payment_id ON public.receipts USING btree (payment_id);


--
-- Name: ix_receipts_receipt_number; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_receipts_receipt_number ON public.receipts USING btree (receipt_number);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: account_transactions account_transactions_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.account_transactions
    ADD CONSTRAINT account_transactions_account_id_fkey FOREIGN KEY (account_id) REFERENCES public.apartment_accounts(id) ON DELETE CASCADE;


--
-- Name: apartment_accounts apartment_accounts_apartment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.apartment_accounts
    ADD CONSTRAINT apartment_accounts_apartment_id_fkey FOREIGN KEY (apartment_id) REFERENCES public.apartments(id) ON DELETE CASCADE;


--
-- Name: audit_logs audit_logs_apartment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_apartment_id_fkey FOREIGN KEY (apartment_id) REFERENCES public.apartments(id) ON DELETE SET NULL;


--
-- Name: audit_logs audit_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: payments fk_payments_voided_by_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT fk_payments_voided_by_id FOREIGN KEY (voided_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: obligations obligations_apartment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.obligations
    ADD CONSTRAINT obligations_apartment_id_fkey FOREIGN KEY (apartment_id) REFERENCES public.apartments(id) ON DELETE CASCADE;


--
-- Name: payments payments_apartment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_apartment_id_fkey FOREIGN KEY (apartment_id) REFERENCES public.apartments(id) ON DELETE CASCADE;


--
-- Name: payments payments_collected_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_collected_by_id_fkey FOREIGN KEY (collected_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: receipts receipts_issued_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.receipts
    ADD CONSTRAINT receipts_issued_by_id_fkey FOREIGN KEY (issued_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: receipts receipts_original_receipt_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.receipts
    ADD CONSTRAINT receipts_original_receipt_id_fkey FOREIGN KEY (original_receipt_id) REFERENCES public.receipts(id) ON DELETE SET NULL;


--
-- Name: receipts receipts_payment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.receipts
    ADD CONSTRAINT receipts_payment_id_fkey FOREIGN KEY (payment_id) REFERENCES public.payments(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict 2ggsVh9547S3B9ADWQ2lAAgavGHQd0Em8PYe3n3Gs0cYOrq1CLrP6YkIbBMIeqs

