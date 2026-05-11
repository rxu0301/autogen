import {
  IsString,
  IsNotEmpty,
  IsOptional,
  IsBoolean,
  IsInt,
  Min,
  Max,
  MaxLength,
} from 'class-validator';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export class GenerateContentDto {
  @ApiProperty({ description: '사용자 관심사', example: '헬스, 다이어트' })
  @IsString()
  @IsNotEmpty()
  @MaxLength(200)
  interest: string;

  @ApiProperty({ description: '콘텐츠 목적', example: '팔로워 증가' })
  @IsString()
  @IsNotEmpty()
  @MaxLength(200)
  goal: string;

  @ApiProperty({ description: '타겟 시청자', example: '20~30대 직장인' })
  @IsString()
  @IsNotEmpty()
  @MaxLength(200)
  target_audience: string;

  @ApiProperty({
    description: '플랫폼 (TikTok, Instagram, YouTube 등)',
    example: 'TikTok',
  })
  @IsString()
  @IsNotEmpty()
  platform: string;

  @ApiProperty({ description: '콘텐츠 톤 (예: 유머, 정보, 감성)', example: '유머' })
  @IsString()
  @IsNotEmpty()
  @MaxLength(100)
  tone: string;

  @ApiProperty({ description: '영상 길이 (예: 15초, 30초, 1분)', example: '30초' })
  @IsString()
  @IsNotEmpty()
  @MaxLength(50)
  duration: string;

  @ApiPropertyOptional({ description: '참고 키워드 (쉼표 구분)', example: '홈트, 다이어트' })
  @IsOptional()
  @IsString()
  @MaxLength(500)
  keywords?: string;

  @ApiPropertyOptional({ description: 'Ollama LLM 사용 여부', default: true })
  @IsOptional()
  @IsBoolean()
  use_llm?: boolean;
}

export class SimilarContentDto {
  @ApiProperty({ description: '검색 쿼리 텍스트', example: '다이어트 챌린지' })
  @IsString()
  @IsNotEmpty()
  @MaxLength(500)
  query: string;

  @ApiPropertyOptional({ description: '반환할 최대 결과 수', default: 5, minimum: 1, maximum: 20 })
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(20)
  top_k?: number;
}
