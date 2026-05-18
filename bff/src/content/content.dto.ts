import {
  IsString,
  IsNotEmpty,
  IsOptional,
  IsArray,
  IsInt,
  Min,
  Max,
  MaxLength,
  IsIn,
} from 'class-validator';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

// ---------------------------------------------------------------------------
// Step 1: 뉴스 검색
// ---------------------------------------------------------------------------

export class NewsSearchDto {
  @ApiProperty({ description: '검색할 주제', example: '인공지능' })
  @IsString()
  @IsNotEmpty()
  @MaxLength(200)
  topic: string;
}

// ---------------------------------------------------------------------------
// Step 2-A: 요약본 생성
// ---------------------------------------------------------------------------

export class SummaryGenerateDto {
  @ApiProperty({ description: '선택한 뉴스 ID' })
  @IsString()
  @IsNotEmpty()
  news_id: string;

  @ApiProperty({ description: '뉴스 제목' })
  @IsString()
  @IsNotEmpty()
  @MaxLength(300)
  news_title: string;

  @ApiProperty({ description: '뉴스 본문/요약' })
  @IsString()
  @IsNotEmpty()
  @MaxLength(2000)
  news_content: string;

  @ApiPropertyOptional({ description: "출력 언어: 'ko' | 'en'", enum: ['ko', 'en'] })
  @IsOptional()
  @IsString()
  @IsIn(['ko', 'en'])
  language?: string;
}

// ---------------------------------------------------------------------------
// Step 2-B: 스크립트 생성
// ---------------------------------------------------------------------------

export class ScriptGenerateDto {
  @ApiProperty({ description: '선택한 뉴스 ID', example: 'news_abc123' })
  @IsString()
  @IsNotEmpty()
  news_id: string;

  @ApiProperty({ description: '뉴스 제목', example: 'AI가 의료 진단 정확도 95% 달성' })
  @IsString()
  @IsNotEmpty()
  @MaxLength(300)
  news_title: string;

  @ApiProperty({ description: '뉴스 본문/요약', example: '...' })
  @IsString()
  @IsNotEmpty()
  @MaxLength(2000)
  news_content: string;

  @ApiProperty({
    description: "영상 길이: '20초' | '30초' | '1분'",
    example: '30초',
    enum: ['20초', '30초', '1분'],
  })
  @IsString()
  @IsIn(['20초', '30초', '1분'])
  duration: string;

  @ApiPropertyOptional({
    description: "출력 언어: 'ko' (한국어) | 'en' (영어)",
    example: 'ko',
    enum: ['ko', 'en'],
  })
  @IsOptional()
  @IsString()
  @IsIn(['ko', 'en'])
  language?: string;
}

// ---------------------------------------------------------------------------
// Step 3: 썸네일 프롬프트 생성
// ---------------------------------------------------------------------------

export class ThumbnailPromptDto {
  @ApiProperty({ description: '뉴스 ID', example: 'news_abc123' })
  @IsString()
  @IsNotEmpty()
  news_id: string;

  @ApiProperty({ description: '뉴스 제목', example: 'AI가 의료 진단 정확도 95% 달성' })
  @IsString()
  @IsNotEmpty()
  @MaxLength(300)
  news_title: string;

  @ApiProperty({ description: '선택된 요약 스크립트', example: 'AI가 드디어...' })
  @IsString()
  @IsNotEmpty()
  @MaxLength(2000)
  selected_script: string;

  @ApiPropertyOptional({ description: '관련 해시태그 목록', example: ['#AI', '#의료'] })
  @IsOptional()
  @IsArray()
  @IsString({ each: true })
  hashtags?: string[];
}

// ---------------------------------------------------------------------------
// Step 4: 결과 저장
// ---------------------------------------------------------------------------

export class SaveResultDto {
  @ApiProperty({ description: '검색 주제' })
  @IsString()
  @IsNotEmpty()
  topic: string;

  @ApiProperty({ description: '선택된 뉴스 객체' })
  news: Record<string, unknown>;

  @ApiProperty({ description: '선택된 스크립트 버전 객체' })
  selected_script: Record<string, unknown>;

  @ApiProperty({ description: '선택된 영상 길이' })
  @IsString()
  @IsNotEmpty()
  duration: string;

  @ApiProperty({ description: '썸네일 프롬프트 목록' })
  thumbnail_prompts: Record<string, unknown>[];

  @ApiPropertyOptional({ description: '해시태그 목록' })
  @IsOptional()
  @IsArray()
  hashtags?: string[];
}

// ---------------------------------------------------------------------------
// Step 5: 라이브러리 조회
// ---------------------------------------------------------------------------

export class LibraryQueryDto {
  @ApiPropertyOptional({ description: '필터링할 해시태그', example: '#AI' })
  @IsOptional()
  @IsString()
  hashtag?: string;

  @ApiPropertyOptional({ description: '최대 반환 개수', default: 20 })
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(100)
  limit?: number;
}
