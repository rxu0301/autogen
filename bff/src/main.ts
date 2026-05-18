import { NestFactory } from '@nestjs/core';
import { ValidationPipe, Logger } from '@nestjs/common';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';
import { AppModule } from './app.module';

async function bootstrap() {
  const logger = new Logger('Bootstrap');
  const app = await NestFactory.create(AppModule, { logger: ['log', 'warn', 'error', 'debug'] });

  // CORS
  const corsOrigin = process.env.CORS_ORIGIN || 'http://localhost:3000';
  app.enableCors({ origin: corsOrigin });
  logger.log(`CORS enabled for origin: ${corsOrigin}`);

  // Global prefix
  app.setGlobalPrefix('api');

  // Global validation pipe — strips unknown fields and validates DTOs
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: false,
      transform: true,
      transformOptions: { enableImplicitConversion: true },
    }),
  );

  // Swagger / OpenAPI documentation
  const swaggerConfig = new DocumentBuilder()
    .setTitle('뉴스 숏폼 에이전트 BFF API')
    .setDescription('뉴스 검색 · 스크립트 생성 · 썸네일 프롬프트 생성 · 라이브러리 관리')
    .setVersion('2.0')
    .addTag('news', '뉴스 검색 및 콘텐츠 생성')
    .addTag('health', '헬스 체크')
    .build();
  const document = SwaggerModule.createDocument(app, swaggerConfig);
  SwaggerModule.setup('api/docs', app, document);

  const port = process.env.PORT || 4000;
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';

  await app.listen(port);
  logger.log(`BFF server running on http://localhost:${port}`);
  logger.log(`Swagger docs available at http://localhost:${port}/api/docs`);
  logger.log(`Proxying requests to backend: ${backendUrl}`);
}
bootstrap();
