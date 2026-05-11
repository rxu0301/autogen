import React, { useState } from 'react';
import { ContentRequest } from '../types/content';

const PLATFORMS = ['TikTok', 'Instagram', 'YouTube', 'Shorts'];
const DURATIONS = ['15초', '30초', '60초'];

interface Props {
  onSubmit: (req: ContentRequest) => void;
  loading: boolean;
}

const defaultForm: ContentRequest = {
  interest: '',
  goal: '',
  target_audience: '',
  platform: 'TikTok',
  tone: '',
  duration: '15초',
  keywords: '',
  use_llm: true,
};

const styles = {
  form: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: 16,
  },
  fieldGroup: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: 4,
  },
  label: {
    fontSize: 13,
    fontWeight: 600,
    color: '#374151',
    letterSpacing: '0.01em',
  },
  required: {
    color: '#ef4444',
    marginLeft: 2,
  },
  input: {
    padding: '9px 12px',
    border: '1px solid #d1d5db',
    borderRadius: 8,
    fontSize: 14,
    color: '#111827',
    background: '#fff',
    outline: 'none',
    transition: 'border-color 0.15s, box-shadow 0.15s',
    width: '100%',
    boxSizing: 'border-box' as const,
  },
  inputFocus: {
    borderColor: '#6366f1',
    boxShadow: '0 0 0 3px rgba(99,102,241,0.15)',
  },
  select: {
    padding: '9px 12px',
    border: '1px solid #d1d5db',
    borderRadius: 8,
    fontSize: 14,
    color: '#111827',
    background: '#fff',
    outline: 'none',
    cursor: 'pointer',
    width: '100%',
    boxSizing: 'border-box' as const,
    appearance: 'none' as const,
    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%236b7280' d='M6 8L1 3h10z'/%3E%3C/svg%3E")`,
    backgroundRepeat: 'no-repeat',
    backgroundPosition: 'right 12px center',
    paddingRight: 36,
  },
  row: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 12,
  },
  checkboxRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '10px 12px',
    background: '#f9fafb',
    borderRadius: 8,
    border: '1px solid #e5e7eb',
    cursor: 'pointer',
  },
  checkbox: {
    width: 16,
    height: 16,
    cursor: 'pointer',
    accentColor: '#6366f1',
  },
  checkboxLabel: {
    fontSize: 14,
    color: '#374151',
    cursor: 'pointer',
    userSelect: 'none' as const,
  },
  submitBtn: {
    padding: '12px 24px',
    background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
    color: '#fff',
    border: 'none',
    borderRadius: 10,
    fontSize: 15,
    fontWeight: 600,
    cursor: 'pointer',
    transition: 'opacity 0.15s, transform 0.1s',
    marginTop: 4,
  },
  submitBtnDisabled: {
    opacity: 0.6,
    cursor: 'not-allowed',
  },
  hint: {
    fontSize: 12,
    color: '#9ca3af',
    marginTop: 2,
  },
};

function Field({
  label,
  required,
  hint,
  children,
}: {
  label: string;
  required?: boolean;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div style={styles.fieldGroup}>
      <label style={styles.label}>
        {label}
        {required && <span style={styles.required}>*</span>}
      </label>
      {children}
      {hint && <span style={styles.hint}>{hint}</span>}
    </div>
  );
}

function FocusInput(props: React.InputHTMLAttributes<HTMLInputElement>) {
  const [focused, setFocused] = useState(false);
  return (
    <input
      {...props}
      style={{
        ...styles.input,
        ...(focused ? styles.inputFocus : {}),
      }}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
    />
  );
}

export default function ContentForm({ onSubmit, loading }: Props) {
  const [form, setForm] = useState<ContentRequest>(defaultForm);

  const set =
    (k: keyof ContentRequest) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setForm((f) => ({ ...f, [k]: e.target.value }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(form);
  };

  return (
    <form onSubmit={handleSubmit} style={styles.form}>
      <Field label="관심사" required hint="예: 헬스, 다이어트, 요리">
        <FocusInput
          value={form.interest}
          onChange={set('interest')}
          required
          placeholder="헬스, 다이어트"
        />
      </Field>

      <Field label="콘텐츠 목적" required hint="예: 팔로워 증가, 브랜드 인지도">
        <FocusInput
          value={form.goal}
          onChange={set('goal')}
          required
          placeholder="팔로워 증가"
        />
      </Field>

      <Field label="타겟 시청자" required hint="예: 20대 여성, 직장인">
        <FocusInput
          value={form.target_audience}
          onChange={set('target_audience')}
          required
          placeholder="20대 여성"
        />
      </Field>

      <div style={styles.row}>
        <Field label="플랫폼">
          <select value={form.platform} onChange={set('platform')} style={styles.select}>
            {PLATFORMS.map((p) => (
              <option key={p}>{p}</option>
            ))}
          </select>
        </Field>

        <Field label="영상 길이">
          <select value={form.duration} onChange={set('duration')} style={styles.select}>
            {DURATIONS.map((d) => (
              <option key={d}>{d}</option>
            ))}
          </select>
        </Field>
      </div>

      <Field label="콘텐츠 톤" required hint="예: 자극적 + 유머, 감성적, 정보 전달">
        <FocusInput
          value={form.tone}
          onChange={set('tone')}
          required
          placeholder="자극적 + 유머"
        />
      </Field>

      <Field label="키워드" hint="쉼표로 구분 (선택사항)">
        <FocusInput
          value={form.keywords}
          onChange={set('keywords')}
          placeholder="뱃살, 홈트, 다이어트"
        />
      </Field>

      <label style={styles.checkboxRow}>
        <input
          type="checkbox"
          checked={form.use_llm}
          onChange={(e) => setForm((f) => ({ ...f, use_llm: e.target.checked }))}
          style={styles.checkbox}
        />
        <span style={styles.checkboxLabel}>Ollama LLM 사용 (미체크 시 폴백 모드)</span>
      </label>

      <button
        type="submit"
        disabled={loading}
        style={{
          ...styles.submitBtn,
          ...(loading ? styles.submitBtnDisabled : {}),
        }}
      >
        {loading ? '⏳ 생성 중...' : '✨ 콘텐츠 생성'}
      </button>
    </form>
  );
}
